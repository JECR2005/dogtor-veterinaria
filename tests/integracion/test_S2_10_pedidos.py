"""S2-10 y S2-11 · UI-09 Pedidos de compra y UI-10 Recepción: captura, edición, cancelación y validaciones."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from inventario.models import Lote, PedidoCompra
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def admin(client, crear_usuario):
    usuario = crear_usuario("administrador", rol=Rol.ADMINISTRADOR)
    client.force_login(usuario)
    client.empleado = usuario.empleado
    return client


@pytest.fixture
def catalogo():
    proveedor = fabricas.proveedor("Distribuidora")
    vacuna = fabricas.producto("VAC-003", "Vacuna triple felina", stock_minimo=5, proveedor=proveedor)
    collar = fabricas.producto("ACC-001", "Collar", categoria="Accesorio", unidad_medida="Pieza")
    return proveedor, vacuna, collar


def _datos(proveedor, *partidas, filas=6):
    datos = {
        "proveedor": proveedor.pk if proveedor else "",
        "partidas-TOTAL_FORMS": str(filas),
        "partidas-INITIAL_FORMS": "0",
        "partidas-MIN_NUM_FORMS": "6",
        "partidas-MAX_NUM_FORMS": "40",
    }
    for i in range(filas):
        producto, cantidad, costo = partidas[i] if i < len(partidas) else ("", "", "")
        datos.update(
            {
                f"partidas-{i}-producto": getattr(producto, "pk", producto),
                f"partidas-{i}-cantidad": cantidad,
                f"partidas-{i}-costo_unitario": costo,
            }
        )
    return datos


def test_S2_10_registra_el_pedido_con_su_total_e_ignora_filas_vacias(admin, catalogo):
    proveedor, vacuna, collar = catalogo
    respuesta = admin.post(
        "/compras/pedidos/nuevo/",
        _datos(proveedor, (vacuna, 20, "140.00"), (collar, 3, "55.50")),
        follow=True,
    )
    pedido = PedidoCompra.objects.get()
    assert (pedido.estado, pedido.total, pedido.detalles.count()) == ("Pendiente", Decimal("2966.50"), 2)
    assert f"Pedido {pedido.folio} registrado por $2,966.50." in respuesta.content.decode()


@pytest.mark.parametrize(
    "partidas, mensaje",
    [
        ([], "Agregue al menos un producto al pedido."),
        ([("vacuna", 20, "")], "Capture el costo."),
        ([("vacuna", 0, "10")], "mayor o igual a 1"),
        ([("vacuna", 2, "10"), ("vacuna", 3, "10")], "Un producto aparece en dos partidas"),
    ],
)
def test_S2_10_validaciones_del_pedido(admin, catalogo, partidas, mensaje):
    proveedor, vacuna, _ = catalogo
    partidas = [(vacuna if p == "vacuna" else p, c, costo) for p, c, costo in partidas]
    contenido = admin.post("/compras/pedidos/nuevo/", _datos(proveedor, *partidas)).content.decode()
    assert mensaje in contenido
    assert not PedidoCompra.objects.exists()


def test_S2_10_no_ofrece_proveedores_dados_de_baja(admin, catalogo):
    fabricas.proveedor("Viejo proveedor", activo=False)
    contenido = admin.get("/compras/pedidos/nuevo/").content.decode()
    assert "Distribuidora" in contenido and "Viejo proveedor" not in contenido


def test_S2_10_pedir_desde_una_alerta_trae_el_producto_y_su_proveedor(admin, catalogo):
    proveedor, vacuna, _ = catalogo
    respuesta = admin.get("/compras/pedidos/nuevo/", {"producto": vacuna.pk})
    assert respuesta.context["formulario"].initial["proveedor"] == proveedor
    assert respuesta.context["partidas"].forms[0].initial["producto"] == vacuna
    assert f"?producto={vacuna.pk}" in admin.get("/inventario/alertas/").content.decode()  # botón «Pedir»


def test_S2_10_editar_un_pedido_pendiente_reemplaza_partidas_y_total(admin, catalogo):
    proveedor, vacuna, collar = catalogo
    pedido = fabricas.pedido(proveedor, admin.empleado, [(vacuna, 20, "140")])
    edicion = admin.get(f"/compras/pedidos/{pedido.pk}/editar/")
    assert edicion.context["partidas"].forms[0].initial["cantidad"] == 20
    admin.post(f"/compras/pedidos/{pedido.pk}/editar/", _datos(proveedor, (collar, 4, "50")))
    pedido.refresh_from_db()
    assert pedido.total == Decimal("200.00")
    assert [d.producto for d in pedido.detalles.all()] == [collar]


def test_S2_10_cancelar_pide_confirmacion_y_despues_ya_no_se_recibe_ni_edita(admin, catalogo):
    proveedor, vacuna, _ = catalogo
    pedido = fabricas.pedido(proveedor, admin.empleado, [(vacuna, 20, "140")])
    assert "¿Cancelar el pedido" in admin.get(f"/compras/pedidos/{pedido.pk}/cancelar/").content.decode()
    assert PedidoCompra.objects.get().estado == "Pendiente"  # ver la confirmación no cancela
    respuesta = admin.post(f"/compras/pedidos/{pedido.pk}/cancelar/", follow=True)
    assert f"Pedido {pedido.folio} cancelado." in respuesta.content.decode()
    for accion in ("recibir", "editar", "cancelar"):
        respuesta = admin.get(f"/compras/pedidos/{pedido.pk}/{accion}/", follow=True)
        assert "ya está cancelado" in respuesta.content.decode(), accion


def test_S2_10_lista_por_estado(admin, catalogo):
    proveedor, vacuna, _ = catalogo
    pendiente = fabricas.pedido(proveedor, admin.empleado, [(vacuna, 1, "1")])
    cancelado = fabricas.pedido(proveedor, admin.empleado, [(vacuna, 2, "1")])
    admin.post(f"/compras/pedidos/{cancelado.pk}/cancelar/", follow=True)  # consume el aviso «cancelado»
    contenido = admin.get("/compras/pedidos/", {"estado": "Pendiente"}).content.decode()
    assert pendiente.folio in contenido and cancelado.folio not in contenido
    assert "Pedidos por recibir" in contenido


# --- S2-11 · Validaciones de la recepción ------------------------------------------------
def _recibir(admin, pedido, *filas):
    datos = {}
    for detalle, (cantidad, lote, caducidad) in zip(
        pedido.detalles.order_by("id_detalle_pedido"), filas, strict=True
    ):
        datos.update(
            {
                f"p{detalle.pk}-cantidad_recibida": cantidad,
                f"p{detalle.pk}-numero_lote": lote,
                f"p{detalle.pk}-fecha_caducidad": caducidad.isoformat() if caducidad else "",
            }
        )
    return admin.post(f"/compras/pedidos/{pedido.pk}/recibir/", datos).content.decode()


@pytest.mark.parametrize(
    "fila, mensaje",
    [
        ((21, "L-1", 30), "Se pidieron 20; no puede recibir más."),
        ((20, "", 30), "Capture el número de lote."),
        ((20, "L-1", None), "Capture la caducidad."),
        ((20, "L-1", -1), "Ya está vencido; no se puede recibir (RD-03)."),
        ((0, "", None), "No llegó ningún producto"),
    ],
)
def test_S2_11_validaciones_de_la_recepcion(admin, catalogo, fila, mensaje):
    proveedor, vacuna, _ = catalogo
    pedido = fabricas.pedido(proveedor, admin.empleado, [(vacuna, 20, "140")])
    cantidad, lote, dias = fila
    contenido = _recibir(
        admin, pedido, (cantidad, lote, None if dias is None else HOY + timedelta(days=dias))
    )
    assert mensaje in contenido
    assert not Lote.objects.exists()
    assert PedidoCompra.objects.get().estado == "Pendiente"


def test_S2_11_un_accesorio_se_recibe_sin_caducidad(admin, catalogo):
    proveedor, _, collar = catalogo
    pedido = fabricas.pedido(proveedor, admin.empleado, [(collar, 4, "50")])
    _recibir(admin, pedido, (4, "COL-1", None))
    lote = Lote.objects.get()
    assert (lote.numero_lote, lote.fecha_caducidad, lote.cantidad_disponible) == ("COL-1", None, Decimal("4"))
