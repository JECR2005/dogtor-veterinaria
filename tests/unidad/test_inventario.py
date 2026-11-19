"""S2-06 y S2-07 · Reglas de lote y descuento (Tabla 4.12): TU-06 a TU-09, más entradas y ajustes (S2-08).

TU-06 Lote.estaVencido: caducidad de ayer y de hoy → ayer vencido; hoy vigente (RD-03).
TU-07 Producto.stockDisponible: lote vigente con 10 y vencido con 5 → stock disponible de 10 (RD-05).
TU-08 Selección de lote: A con 3 caduca antes, B con 10 después; se piden 2 → A queda en 1, B no cambia.
TU-09 Descuento: se piden 11 con stock de 10 → operación bloqueada; existencias sin cambio.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from catalogos.models import Puesto
from inventario import services
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from tests import fabricas

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

HOY = timezone.localdate()
VENTA = TipoMovimiento.VENTA


@pytest.fixture
def admin():
    return fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Admin")


@pytest.fixture
def vacuna():
    return fabricas.producto("VAC-T", "Vacuna de prueba", stock_minimo=5)


def _existencias(*lotes):
    return [Lote.objects.get(pk=lote.pk).cantidad_disponible for lote in lotes]


# --- S2-06 · TU-06 y TU-07 ----------------------------------------------------------
def test_TU06_el_lote_de_ayer_esta_vencido_y_el_de_hoy_vigente(vacuna):
    ayer = fabricas.lote(vacuna, 5, dias_para_caducar=-1)
    hoy = fabricas.lote(vacuna, 5, dias_para_caducar=0)
    sin_caducidad = fabricas.lote(vacuna, 5, dias_para_caducar=None)
    assert ayer.esta_vencido() is True
    assert hoy.esta_vencido() is False
    assert sin_caducidad.esta_vencido() is False
    assert (ayer.estado(), hoy.estado(), sin_caducidad.estado()) == ("Vencido", "Por caducar", "Vigente")


def test_S2_06_un_lote_sin_existencias_se_muestra_agotado_aunque_haya_caducado(vacuna):
    """Observación de JECR2005 (bloque C): tras desechar el lote vencido decía «Vencido» con 0."""
    assert fabricas.lote(vacuna, 0, dias_para_caducar=-10).estado() == "Agotado"
    assert fabricas.lote(vacuna, 0, dias_para_caducar=60).estado() == "Agotado"


def test_TU07_el_stock_disponible_solo_suma_lotes_vigentes(vacuna):
    fabricas.lote(vacuna, 10, dias_para_caducar=60)
    fabricas.lote(vacuna, 5, dias_para_caducar=-3)
    assert services.stock_disponible(vacuna) == Decimal("10")


def test_TU07_sin_lotes_el_stock_es_cero(vacuna):
    assert services.stock_disponible(vacuna) == Decimal("0")


def test_S2_06_orden_de_descuento_primero_el_que_caduca_antes_y_al_final_el_que_no_caduca(vacuna):
    sin_caducidad = fabricas.lote(vacuna, 1, dias_para_caducar=None, numero="SIN")
    tarde = fabricas.lote(vacuna, 1, dias_para_caducar=200, numero="TARDE")
    pronto = fabricas.lote(vacuna, 1, dias_para_caducar=20, numero="PRONTO")
    fabricas.lote(vacuna, 1, dias_para_caducar=-1, numero="VENCIDO")
    fabricas.lote(vacuna, 0, dias_para_caducar=5, numero="AGOTADO")
    assert list(services.lotes_vigentes(vacuna)) == [pronto, tarde, sin_caducidad]


# --- S2-07 · TU-08 y TU-09 ----------------------------------------------------------
def test_TU08_se_descuenta_del_lote_que_caduca_primero(vacuna, admin):
    lote_b = fabricas.lote(vacuna, 10, dias_para_caducar=200, numero="B")
    lote_a = fabricas.lote(vacuna, 3, dias_para_caducar=30, numero="A")
    descontado = services.descontar(vacuna, 2, admin, VENTA, referencia="T-0001")
    assert [(lote.numero_lote, cantidad) for lote, cantidad in descontado] == [("A", Decimal("2"))]
    assert _existencias(lote_a, lote_b) == [Decimal("1"), Decimal("10")]
    movimiento = MovimientoInventario.objects.get()
    assert (movimiento.lote, movimiento.tipo, movimiento.cantidad, movimiento.referencia) == (
        lote_a,
        VENTA,
        Decimal("-2"),
        "T-0001",
    )


def test_TU09_si_se_pide_mas_que_el_stock_no_se_descuenta_nada(vacuna, admin):
    lote = fabricas.lote(vacuna, 10, dias_para_caducar=60)
    fabricas.lote(vacuna, 5, dias_para_caducar=-1)  # vencido: no cuenta para el stock
    with pytest.raises(services.StockInsuficiente) as error:
        services.descontar(vacuna, 11, admin, VENTA)
    assert str(error.value).startswith(
        "Stock insuficiente: hay 10 Dosis vigentes de «Vacuna de prueba» y se piden 11."
    )
    assert _existencias(lote) == [Decimal("10")]
    assert not MovimientoInventario.objects.exists()


def test_S2_07_un_descuento_puede_tomar_de_varios_lotes(vacuna, admin):
    a = fabricas.lote(vacuna, 3, dias_para_caducar=10, numero="A")
    b = fabricas.lote(vacuna, 10, dias_para_caducar=100, numero="B")
    services.descontar(vacuna, 5, admin, TipoMovimiento.APLICACION)
    assert _existencias(a, b) == [Decimal("0"), Decimal("8")]
    assert sorted(MovimientoInventario.objects.values_list("cantidad", flat=True)) == [
        Decimal("-3"),
        Decimal("-2"),
    ]


def test_S2_07_descuenta_fracciones_de_mL(admin):
    ivermectina = fabricas.producto("MED-ML", "Ivermectina", unidad_medida="mL")
    lote = fabricas.lote(ivermectina, "10.00")
    services.descontar(ivermectina, "0.5", admin, TipoMovimiento.APLICACION)
    assert _existencias(lote) == [Decimal("9.50")]


@pytest.mark.parametrize(
    "cantidad, mensaje", [(0, "mayor que cero"), (-1, "mayor que cero"), ("0.001", "2 decimales")]
)
def test_S2_07_rechaza_cantidades_invalidas(vacuna, admin, cantidad, mensaje):
    fabricas.lote(vacuna, 10)
    with pytest.raises(services.ErrorInventario, match=mensaje):
        services.descontar(vacuna, cantidad, admin, VENTA)


def test_S2_07_solo_ventas_y_aplicaciones_descuentan(vacuna, admin):
    fabricas.lote(vacuna, 10)
    with pytest.raises(ValueError):
        services.descontar(vacuna, 1, admin, TipoMovimiento.AJUSTE)


# --- S2-08 · Entradas y ajustes ---------------------------------------------------------
def test_S2_08_la_entrada_crea_el_lote_y_su_movimiento(vacuna, admin):
    caducidad = HOY + timedelta(days=300)
    lote = services.registrar_entrada(vacuna, " l-77 ", "12", admin, caducidad, referencia="Factura 9")
    assert (lote.numero_lote, lote.fecha_caducidad, lote.cantidad_disponible) == (
        "L-77",
        caducidad,
        Decimal("12"),
    )
    entrada = lote.movimientos.get()
    assert (entrada.tipo, entrada.cantidad, entrada.referencia) == ("Entrada", Decimal("12"), "Factura 9")


def test_S2_08_la_entrada_suma_al_mismo_lote_y_rechaza_otra_caducidad(vacuna, admin):
    caducidad = HOY + timedelta(days=300)
    services.registrar_entrada(vacuna, "L-1", 4, admin, caducidad)
    lote = services.registrar_entrada(vacuna, "l-1", 6, admin, caducidad)
    assert lote.cantidad_disponible == Decimal("10") and Lote.objects.count() == 1
    with pytest.raises(services.ErrorInventario, match="ya existe con otra caducidad"):
        services.registrar_entrada(vacuna, "L-1", 1, admin, caducidad + timedelta(days=1))
    assert lote.movimientos.count() == 2


def test_S2_08_el_ajuste_exige_motivo_y_no_deja_el_lote_en_negativo(vacuna, admin):
    lote = fabricas.lote(vacuna, 10)
    with pytest.raises(services.ErrorInventario, match="motivo"):
        services.ajustar(lote, -1, "  ", admin)
    with pytest.raises(services.ErrorInventario, match="en negativo"):
        services.ajustar(lote, -11, "Conteo físico", admin)
    with pytest.raises(services.ErrorInventario, match="cero"):
        services.ajustar(lote, 0, "Conteo físico", admin)
    ajustado = services.ajustar(lote, "-2.50", "Frasco roto", admin)
    assert ajustado.cantidad_disponible == Decimal("7.50")
    ajuste = MovimientoInventario.objects.get()
    assert (ajuste.tipo, ajuste.cantidad, ajuste.motivo) == ("Ajuste", Decimal("-2.50"), "Frasco roto")


def test_S2_08_el_kardex_cuadra_con_las_existencias(vacuna, admin):
    lote = services.registrar_entrada(vacuna, "K-1", 20, admin, HOY + timedelta(days=90))
    services.descontar(vacuna, 3, admin, VENTA)
    services.ajustar(lote, 1, "Conteo físico", admin)
    lote.refresh_from_db()
    assert lote.cantidad_disponible == Decimal("18")
    assert sum(lote.movimientos.values_list("cantidad", flat=True)) == lote.cantidad_disponible


def test_S2_08_un_movimiento_no_se_puede_modificar_RD07(vacuna, admin):
    lote = services.registrar_entrada(vacuna, "R-1", 5, admin, HOY + timedelta(days=90))
    movimiento = lote.movimientos.get()
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        MovimientoInventario.objects.filter(pk=movimiento.pk).update(cantidad=50)


# --- S2-09 · Alertas ---------------------------------------------------------------------
def test_S2_09_alertas_de_stock_bajo_caducidad_y_vencidos(admin):
    bajo = fabricas.producto("B-1", "Bajo", stock_minimo=10)
    fabricas.lote(bajo, 4, 200)
    caduca = fabricas.producto("C-1", "Caduca", stock_minimo=1)
    lote_caduca = fabricas.lote(caduca, 5, 30)
    fabricas.lote(caduca, 5, 31)
    vencido = fabricas.producto("V-1", "Vencido", stock_minimo=0)
    lote_vencido = fabricas.lote(vencido, 2, -1)
    fabricas.lote(vencido, 0, -5)  # vencido pero vacío: no hay nada que desechar
    inactivo = fabricas.producto("I-1", "Inactivo", stock_minimo=10, activo=False)
    fabricas.lote(inactivo, 1, 2)

    avisos = services.alertas()
    assert [p.codigo for p in avisos["stock_bajo"]] == ["B-1", "V-1"]
    assert avisos["por_caducar"] == [lote_caduca]
    assert avisos["vencidos"] == [lote_vencido]
