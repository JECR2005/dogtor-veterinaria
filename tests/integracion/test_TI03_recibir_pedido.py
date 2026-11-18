"""TI-03 · Inventario y compras (Tabla 4.13): recibir un pedido de compra con dos productos.

Criterio: se crean dos lotes con caducidad y sus movimientos de entrada; las existencias suben y las alertas
se recalculan (RF-11, RF-12).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from catalogos.models import Puesto
from inventario import services
from inventario.models import Lote, MovimientoInventario, PedidoCompra
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def escenario():
    admin = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Admin")
    proveedor = fabricas.proveedor("Distribuidora")
    vacuna = fabricas.producto("VAC-003", "Vacuna triple felina", stock_minimo=5)
    fabricas.lote(vacuna, 3, 200, numero="VIEJO")  # 3 < 5: stock bajo antes de recibir
    amoxicilina = fabricas.producto("MED-001", "Amoxicilina", categoria="Medicamento", stock_minimo=30)
    pedido = fabricas.pedido(proveedor, admin, [(vacuna, 20, "140"), (amoxicilina, 60, "9")])
    return admin, pedido, vacuna, amoxicilina


def _recepcion(pedido, *filas):
    detalles = list(pedido.detalles.order_by("id_detalle_pedido"))
    return {d.pk: fila for d, fila in zip(detalles, filas, strict=True)}


def test_TI03_recibir_un_pedido_con_dos_productos(escenario):
    admin, pedido, vacuna, amoxicilina = escenario
    assert [p.codigo for p in services.alertas()["stock_bajo"]] == ["MED-001", "VAC-003"]
    caducidad = HOY + timedelta(days=365)

    lotes = services.recibir_pedido(
        pedido, admin, _recepcion(pedido, (20, "vtf-2611", caducidad), (60, "AMX-77", caducidad))
    )

    assert {(lote.numero_lote, lote.fecha_caducidad, lote.cantidad_disponible) for lote in lotes} == {
        ("VTF-2611", caducidad, Decimal("20")),
        ("AMX-77", caducidad, Decimal("60")),
    }
    entradas = MovimientoInventario.objects.filter(referencia=pedido.folio)
    assert sorted((m.tipo, m.cantidad) for m in entradas) == [
        ("Entrada", Decimal("20")),
        ("Entrada", Decimal("60")),
    ]
    assert services.stock_disponible(vacuna) == Decimal("23")
    assert services.stock_disponible(amoxicilina) == Decimal("60")
    assert services.alertas()["stock_bajo"] == []  # las alertas se recalculan
    pedido.refresh_from_db()
    assert (pedido.estado, pedido.fecha_recepcion) == ("Recibido", HOY)
    assert list(
        pedido.detalles.order_by("id_detalle_pedido").values_list("cantidad_recibida", flat=True)
    ) == [20, 60]


def test_TI03_si_una_partida_falla_no_se_crea_ningun_lote(escenario):
    admin, pedido, vacuna, _ = escenario
    caducidad = HOY + timedelta(days=365)
    Lote.objects.create(
        producto=pedido.detalles.last().producto,
        numero_lote="AMX-77",
        fecha_caducidad=HOY + timedelta(days=20),
    )
    with pytest.raises(services.ErrorInventario, match="ya existe con otra caducidad"):
        services.recibir_pedido(
            pedido, admin, _recepcion(pedido, (20, "VTF-2611", caducidad), (60, "AMX-77", caducidad))
        )
    assert not Lote.objects.filter(numero_lote="VTF-2611").exists()  # la primera partida también se revirtió
    assert not MovimientoInventario.objects.exists()
    assert PedidoCompra.objects.get(pk=pedido.pk).estado == "Pendiente"


def test_TI03_recibir_desde_la_pantalla(client, crear_usuario, escenario):
    _, pedido, vacuna, _ = escenario
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    caducidad = (HOY + timedelta(days=365)).isoformat()
    datos = {}
    for detalle, (cantidad, lote) in zip(
        pedido.detalles.order_by("id_detalle_pedido"), [(20, "VTF-2611"), (0, "")], strict=True
    ):
        prefijo = f"p{detalle.pk}"
        datos.update(
            {
                f"{prefijo}-cantidad_recibida": cantidad,
                f"{prefijo}-numero_lote": lote,
                f"{prefijo}-fecha_caducidad": caducidad,
            }
        )
    respuesta = client.post(f"/compras/pedidos/{pedido.pk}/recibir/", datos, follow=True)
    contenido = respuesta.content.decode()
    assert f"Pedido {pedido.folio} recibido: 1 lote con su entrada" in contenido
    assert "Lotes que entraron con este pedido" in contenido and "VTF-2611" in contenido
    assert services.stock_disponible(vacuna) == Decimal("23")
    assert list(
        pedido.detalles.order_by("id_detalle_pedido").values_list("cantidad_recibida", flat=True)
    ) == [20, 0]
