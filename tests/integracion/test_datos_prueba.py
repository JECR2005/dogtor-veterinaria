"""S0-19 · El comando de datos ficticios es repetible y respeta las reglas del modelo."""

import pytest
from django.core.management import call_command

from catalogos.models import Especie, Mascota
from clinico.models import ExpedienteClinico
from inventario.models import Lote, MovimientoInventario
from seguridad.models import Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_S0_carga_los_datos_y_es_idempotente():
    call_command("cargar_datos_prueba", mascotas=20)
    call_command("cargar_datos_prueba", mascotas=20)  # la segunda vez no duplica nada

    assert Especie.objects.count() == 2
    assert Mascota.objects.count() == 20
    assert ExpedienteClinico.objects.count() == 20  # RD-10: un expediente por mascota
    assert set(Usuario.objects.values_list("rol", flat=True)) == {
        "Administrador",
        "Veterinario",
        "Estilista",
        "Recepcionista",
    }
    # Cada lote tiene su movimiento de entrada (trazabilidad del inventario)
    assert MovimientoInventario.objects.filter(tipo="Entrada").count() == Lote.objects.count()


def test_S0_amplia_hasta_la_cantidad_pedida():
    call_command("cargar_datos_prueba", mascotas=10)
    call_command("cargar_datos_prueba", mascotas=25)
    assert Mascota.objects.count() == 25


# --- S2-03 · Datos de P2 (RF-11, RF-12, RD-03, RD-05, D-04) ---------------------
def _vista():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT codigo, stock_disponible, bajo_minimo, caduca_en_30_dias FROM dbo.vista_stock_disponible"
        )
        filas = cursor.fetchall()
    return {codigo: (stock, bool(bajo), bool(caduca)) for codigo, stock, bajo, caduca in filas}


def test_S2_03_los_datos_de_P2_dan_cada_alerta_y_cuadran_con_sus_movimientos():
    from decimal import Decimal

    from django.db.models import Sum

    from inventario.models import PedidoCompra

    call_command("cargar_datos_prueba", mascotas=0)
    call_command("cargar_datos_prueba", mascotas=0)  # repetible: no duplica lotes, ajustes ni pedidos

    vista = _vista()
    assert {c for c, (_, bajo, _) in vista.items() if bajo} == {"VAC-003", "ALI-002"}
    assert {c for c, (_, _, caduca) in vista.items() if caduca} == {"VAC-001", "MED-001"}
    assert vista["VAC-001"][0] == 26  # el lote vencido (4) no cuenta (RD-03)
    assert vista["MED-003"][0] == Decimal("97.50")  # 100 mL menos un ajuste de 2.50 (D-04)
    assert Lote.objects.filter(producto__codigo="ACC-001", fecha_caducidad__isnull=True).count() == 1

    # Kardex: la existencia de cada lote es la suma de sus movimientos
    for lote in Lote.objects.annotate(suma=Sum("movimientos__cantidad")):
        assert lote.cantidad_disponible == lote.suma, lote.numero_lote

    pendientes = PedidoCompra.objects.filter(estado="Pendiente").order_by("total")
    assert [p.total for p in pendientes] == [Decimal("2100.00"), Decimal("3340.00")]
    partidas = pendientes.last().detalles.values_list("producto__codigo", flat=True)
    assert sorted(partidas) == ["MED-001", "VAC-003"]
    assert PedidoCompra.objects.filter(estado="Cancelado").count() == 1
    assert not PedidoCompra.objects.filter(estado="Recibido").exists()
