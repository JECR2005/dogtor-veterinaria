"""S2-13 · Pruebas que intentan violar RD-03 y RD-05 por fuera del servicio de inventario.

El servicio valida antes de escribir (TU-06 a TU-09); aquí se comprueba que, si un código futuro se lo
saltara, la base de datos o las consultas del sistema sigan protegiendo la regla (apartado 4.6.1).
Cada violación va en su propia prueba: tras un error de SQL Server no se hacen más consultas.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.models import F

from catalogos.models import Puesto
from inventario import services
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def lote():
    producto = fabricas.producto("RD-05", "Producto de prueba", stock_minimo=0)
    return fabricas.lote(producto, 3, 100)


@pytest.fixture
def empleado():
    return fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Admin")


def test_S2_13_RD05_la_base_rechaza_un_descuento_que_deja_el_lote_en_negativo(lote):
    """Un UPDATE como el de descontar(), pero sin revisar el stock antes: el CHECK de la base lo detiene."""
    with pytest.raises(IntegrityError, match="CK_lote_cantidad_no_negativa"), transaction.atomic():
        Lote.objects.filter(pk=lote.pk).update(cantidad_disponible=F("cantidad_disponible") - 4)


def test_S2_13_RD05_la_base_rechaza_una_salida_con_cantidad_positiva(lote, empleado):
    with pytest.raises(IntegrityError, match="CK_movimiento_signo_cantidad"), transaction.atomic():
        MovimientoInventario.objects.create(
            lote=lote, empleado=empleado, tipo=TipoMovimiento.VENTA, cantidad=2
        )


def test_S2_13_RD05_la_base_rechaza_un_ajuste_sin_motivo(lote, empleado):
    with pytest.raises(IntegrityError, match="CK_movimiento_ajuste_con_motivo"), transaction.atomic():
        MovimientoInventario.objects.create(
            lote=lote, empleado=empleado, tipo=TipoMovimiento.AJUSTE, cantidad=-1
        )


def test_S2_13_RD03_un_lote_vencido_no_se_descuenta_aunque_sea_el_unico_con_piezas(empleado):
    producto = fabricas.producto("RD-03", "Vacuna vencida", stock_minimo=0)
    vencido = fabricas.lote(producto, 10, -1)
    with pytest.raises(services.StockInsuficiente, match="hay 0 Dosis vigentes"):
        services.descontar(producto, 1, empleado, TipoMovimiento.APLICACION)
    vencido.refresh_from_db()
    assert vencido.cantidad_disponible == Decimal("10")
    with connection.cursor() as cursor:  # la vista de la base tampoco lo cuenta
        cursor.execute(
            "SELECT stock_disponible FROM vista_stock_disponible WHERE id_producto = %s", [producto.pk]
        )
        assert cursor.fetchone()[0] == 0
