"""S2-05 · UI-08 Productos: existencias por lote, distintivos (RI-02), alta y edición (RF-11, RD-03)."""

from decimal import Decimal

import pytest
from django.db import connection
from django.template import Context, Template
from django.utils import timezone

from catalogos.models import Producto
from inventario import services
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

VALIDO = {
    "codigo": " vac 010 ",
    "nombre": "Vacuna  de   prueba",
    "categoria": "Vacuna",
    "unidad_medida": "Dosis",
    "precio_venta": "180.00",
    "stock_minimo": "10",
    "proveedor": "",
    "requiere_receta": "on",
}


@pytest.fixture
def admin(client, crear_usuario):
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    return client


def _anotado(producto):
    return services.productos_con_existencias().get(pk=producto.pk)


# --- Existencias y distintivos (servicio) -----------------------------------------
def test_S2_05_existencias_vigentes_ignoran_lotes_vencidos_y_cuentan_los_que_caducan_hoy():
    producto = fabricas.producto(stock_minimo=5)
    fabricas.lote(producto, 3, dias_para_caducar=0)  # caduca hoy: todavía vigente (RD-03, TU-06)
    fabricas.lote(producto, "2.50", dias_para_caducar=None)  # no caduca
    fabricas.lote(producto, 7, dias_para_caducar=-1)  # venció ayer
    anotado = _anotado(producto)
    assert anotado.stock_vigente == Decimal("5.50")
    assert anotado.cantidad_vencida == Decimal("7.00")
    assert anotado.proxima_caducidad == timezone.localdate()
    assert services.distintivos(anotado) == [("por_caducar", "Caduca hoy"), ("vencido", "Lote vencido")]


@pytest.mark.parametrize(
    "lotes, minimo, esperado",
    [
        ([], 5, [("sin_existencias", "Sin existencias")]),
        ([(4, 200)], 5, [("stock_bajo", "Stock bajo")]),
        ([(5, 200)], 5, []),  # igual al mínimo: no es stock bajo
        ([(20, 30)], 5, [("por_caducar", "Caduca en 30 días")]),  # valor límite de la alerta
        ([(20, 31)], 5, []),
        ([(20, 1)], 5, [("por_caducar", "Caduca en 1 día")]),
        ([(0, 10), (20, 200)], 5, []),  # un lote agotado no avisa de caducidad
    ],
)
def test_S2_05_distintivos(lotes, minimo, esperado):
    producto = fabricas.producto(stock_minimo=minimo)
    for cantidad, dias in lotes:
        fabricas.lote(producto, cantidad, dias)
    assert services.distintivos(_anotado(producto)) == esperado


def test_S2_05_el_calculo_coincide_con_la_vista_de_la_base():
    for i, (cantidad, dias) in enumerate([(3, 10), (8, 200), (4, -5), (6, None)]):
        producto = fabricas.producto(f"P-{i}", stock_minimo=5)
        fabricas.lote(producto, cantidad, dias)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT codigo, stock_disponible, bajo_minimo, caduca_en_30_dias FROM vista_stock_disponible"
        )
        vista = {
            codigo: (stock, bool(bajo), bool(caduca)) for codigo, stock, bajo, caduca in cursor.fetchall()
        }
    for producto in services.productos_con_existencias():
        claves = {clave for clave, _ in services.distintivos(producto)}
        bajo = bool(claves & {"stock_bajo", "sin_existencias"})
        assert vista[producto.codigo] == (producto.stock_vigente, bajo, "por_caducar" in claves), (
            producto.codigo
        )


def test_S2_05_filtros_por_alerta_texto_categoria_e_inactivos():
    bajo = fabricas.producto("B-1", "Vacuna antirrábica", stock_minimo=10)
    fabricas.lote(bajo, 2)
    caduca = fabricas.producto("C-1", "Desparasitante tabletas", categoria="Desparasitante")
    fabricas.lote(caduca, 50, 12)
    vencido = fabricas.producto("V-1", "Shampoo", categoria="Insumo", stock_minimo=0)
    fabricas.lote(vencido, 3, -2)
    inactivo = fabricas.producto("I-1", "Vacuna retirada", activo=False)

    def codigos(**filtros):
        return [p.codigo for p in services.buscar_productos(**filtros)]

    assert codigos(alerta="stock_bajo") == ["V-1", "B-1"]  # sin existencias vigentes también cuenta
    assert codigos(alerta="por_caducar") == ["C-1"]
    assert codigos(alerta="vencido") == ["V-1"]
    assert codigos(texto="antirrabica") == ["B-1"]  # sin acentos (RI-13)
    assert codigos(texto="c-1") == ["C-1"]
    assert codigos(categoria="Insumo") == ["V-1"]
    assert inactivo.codigo not in codigos() and inactivo.codigo in codigos(incluir_inactivos=True)


def test_S2_05_formato_de_existencias():
    plantilla = Template(
        "{% load formato %}{{ a|cantidad }} · {{ b|cantidad }} · {{ c|cantidad }} · {{ d|cantidad }}"
    )
    texto = plantilla.render(Context({"a": Decimal("26.00"), "b": Decimal("97.50"), "c": 1250, "d": None}))
    assert texto == "26 · 97.50 · 1,250 · —"


# --- Pantallas ---------------------------------------------------------------------
def test_S2_05_la_lista_muestra_existencias_y_distintivos_con_texto(admin):
    producto = fabricas.producto(
        "MED-003", "Ivermectina", stock_minimo=20, unidad_medida="mL", requiere_receta=True
    )
    fabricas.lote(producto, "97.50", 15)
    contenido = admin.get("/inventario/productos/").content.decode()
    assert "97.50" in contenido and "mL" in contenido
    assert "Caduca en 15 días" in contenido and "Con receta" in contenido
    assert "bi-arrow-down-circle" not in contenido  # sin distintivo de stock bajo: 97.50 ≥ 20


def test_S2_05_alta_normaliza_el_codigo_y_el_nombre(admin):
    respuesta = admin.post("/inventario/productos/nuevo/", VALIDO, follow=True)
    producto = Producto.objects.get()
    assert (producto.codigo, producto.nombre, producto.requiere_receta) == (
        "VAC010",
        "Vacuna de prueba",
        True,
    )
    assert producto.proveedor is None and producto.activo
    assert "Producto «Vacuna de prueba» registrado." in respuesta.content.decode()


@pytest.mark.parametrize(
    "campo, valor, mensaje",
    [
        ("precio_venta", "-1", "El precio no puede ser negativo."),
        ("precio_venta", "100000", "Revise el precio"),
        ("stock_minimo", "-3", "El stock mínimo no puede ser negativo."),
        ("categoria", "Juguete", "Escoja una opción válida."),
        ("unidad_medida", "", "Este campo es obligatorio."),
    ],
)
def test_S2_05_rechaza_datos_invalidos(admin, campo, valor, mensaje):
    contenido = admin.post("/inventario/productos/nuevo/", {**VALIDO, campo: valor}).content.decode()
    assert mensaje in contenido
    assert not Producto.objects.exists()


def test_S2_05_el_codigo_no_se_repite(admin):
    fabricas.producto("VAC010")
    contenido = admin.post("/inventario/productos/nuevo/", VALIDO).content.decode()
    assert "Ya existe un producto con ese código." in contenido
    assert Producto.objects.count() == 1


def test_S2_05_edicion_cambia_precio_y_proveedor_y_puede_desactivar(admin):
    proveedor = fabricas.proveedor()
    producto = fabricas.producto("VAC010")
    datos = {**VALIDO, "precio_venta": "199.90", "proveedor": proveedor.pk}  # sin «activo» = desactivado
    admin.post(f"/inventario/productos/{producto.pk}/editar/", datos)
    producto.refresh_from_db()
    assert (producto.precio_venta, producto.proveedor, producto.activo) == (
        Decimal("199.90"),
        proveedor,
        False,
    )
    assert "VAC010" not in admin.get("/inventario/productos/").content.decode()
