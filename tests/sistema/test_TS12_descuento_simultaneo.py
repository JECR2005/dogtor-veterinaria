"""S2-13 · Adelanto de TS-12 (Tabla 4.15): dos usuarios descuentan a la vez el último lote (RD-05, RD-09).

Criterio: ninguna existencia queda negativa. Dos hilos, cada uno con su propia conexión a SQL Server, piden la
última pieza al mismo tiempo; descontar() bloquea el producto y sus lotes, así que uno la obtiene y el otro
recibe «Stock insuficiente». TS-12 completo, con ventas y aplicaciones reales, se ejecuta en P5.

Esta prueba necesita datos confirmados (transaction=True) para que los dos hilos los vean. Las tablas son
managed = False y Django no las vacía al terminar, así que la prueba borra lo que creó; para los movimientos
desactiva un momento el disparador de RD-07, solo en la base de pruebas.
"""

import threading
from decimal import Decimal

import pytest
from django.db import connection, connections

from catalogos.models import HorarioLaboral, Puesto
from inventario import services
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from seguridad.models import Usuario
from tests import fabricas

pytestmark = [pytest.mark.sistema, pytest.mark.django_db(transaction=True)]


def _limpiar(producto, empleado):
    with connection.cursor() as cursor:
        cursor.execute("DISABLE TRIGGER dbo.TR_movimiento_inventario_inmutable ON dbo.movimiento_inventario")
        try:
            MovimientoInventario.objects.filter(lote__producto=producto).delete()
        finally:
            cursor.execute(
                "ENABLE TRIGGER dbo.TR_movimiento_inventario_inmutable ON dbo.movimiento_inventario"
            )
    Lote.objects.filter(producto=producto).delete()
    producto.delete()
    HorarioLaboral.objects.filter(empleado=empleado).delete()
    Usuario.objects.filter(empleado=empleado).delete()  # la cuenta que le da fabricas (S5-04)
    empleado.delete()


def test_TS12_dos_descuentos_simultaneos_del_ultimo_lote_no_dejan_existencias_negativas():
    assert connection.settings_dict["NAME"].startswith("test_")  # nunca sobre la base real
    empleado = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="TS12")
    producto = fabricas.producto("TS12-001", "Última pieza", stock_minimo=0)
    lote = fabricas.lote(producto, 1, 100)
    salida = threading.Barrier(2, timeout=30)
    resultados = []

    def vender():
        try:
            salida.wait()
            services.descontar(producto, 1, empleado, TipoMovimiento.VENTA)
            resultados.append("vendió")
        except services.StockInsuficiente:
            resultados.append("sin stock")
        except Exception as error:  # noqa: BLE001 - cualquier otro error debe hacer fallar la prueba
            resultados.append(f"error: {error!r}")
        finally:
            connections.close_all()

    try:
        hilos = [threading.Thread(target=vender) for _ in range(2)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(timeout=60)
        assert sorted(resultados) == ["sin stock", "vendió"]
        lote.refresh_from_db()
        assert lote.cantidad_disponible == Decimal("0")
        assert list(lote.movimientos.values_list("cantidad", flat=True)) == [Decimal("-1")]
    finally:
        _limpiar(producto, empleado)
