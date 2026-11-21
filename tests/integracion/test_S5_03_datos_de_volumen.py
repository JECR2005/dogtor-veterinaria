"""S5-03 · Datos de volumen: consultas y tickets de días pasados sin tocar los escenarios de TA-01 a TA-08."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from agenda.models import Cita
from clinico.models import Aplicacion, Consulta
from clinico.services import avisos_pendientes
from inventario.models import Lote, MovimientoInventario
from ventas.models import Pago, Venta
from ventas.services import citas_por_cobrar, corte_de_caja, siguiente_folio, tickets_con_saldo

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

MOTIVO = "Historial ficticio de P5"


def _escenarios_de_hoy(hoy):
    """Lo que ven los guiones de TA-01 a TA-08: agenda, cobro, caja, inventario y avisos de hoy."""
    corte = corte_de_caja(hoy)
    return {
        "siguiente_folio": siguiente_folio(hoy),
        "por_cobrar": sorted(citas_por_cobrar(hoy).values_list("pk", flat=True)),
        "con_saldo": sorted(tickets_con_saldo().values_list("pk", flat=True)),
        "corte": (corte["totales"], corte["tickets"]),
        "citas_de_hoy_y_futuras": sorted(
            Cita.objects.filter(fecha_hora_inicio__date__gte=hoy).values_list("pk", flat=True)
        ),
        "aplicaciones": Aplicacion.objects.count(),
        "movimientos": MovimientoInventario.objects.count(),
        "existencias": sorted(Lote.objects.values_list("pk", "cantidad_disponible")),
        "avisos": len(list(avisos_pendientes())),
    }


def _dias_habiles(hoy, dias):
    dias = (hoy - timedelta(days=atras) for atras in range(1, dias + 1))
    return [dia for dia in dias if dia.isoweekday() != 7]  # el domingo no hay servicio


def test_S5_03_historial_de_consultas_y_tickets_pagados_en_dias_pasados():
    hoy = timezone.localdate()
    call_command("cargar_datos_prueba", mascotas=30, historial=12)
    call_command("cargar_datos_prueba", mascotas=30, historial=12)  # repetible: no duplica días

    habiles = _dias_habiles(hoy, 12)
    citas = Cita.objects.filter(motivo=MOTIVO)
    assert citas.count() == len(habiles) * 8  # 8 consultas por día, de lunes a sábado
    assert {timezone.localtime(c.fecha_hora_inicio).date() for c in citas} == set(habiles)
    assert all(c.estado == "Completada" and c.empleado.puesto == "Veterinario" for c in citas)

    # Cada cita tiene su consulta firmada y su ticket pagado con un solo abono por el total
    consultas = Consulta.objects.filter(cita__motivo=MOTIVO)
    assert consultas.count() == citas.count()
    assert set(consultas.values_list("estado", flat=True)) == {"Firmada"}
    historicos = Venta.objects.filter(cita__motivo=MOTIVO)
    assert historicos.count() == citas.count()
    for venta in historicos.prefetch_related("pagos", "detalles"):
        assert venta.folio_ticket.startswith("H-") and venta.estado == "Pagada" and venta.saldo == 0
        assert sum(p.monto for p in venta.pagos.all()) == venta.total == Decimal("400.00")
        assert [d.servicio.nombre for d in venta.detalles.all()] == ["Consulta general"]

    # Sin empalmes en la agenda de la veterinaria (RD-02)
    for dia in habiles:
        del_dia = sorted(
            (c for c in citas if timezone.localtime(c.fecha_hora_inicio).date() == dia),
            key=lambda c: c.fecha_hora_inicio,
        )
        for anterior, siguiente in zip(del_dia, del_dia[1:], strict=False):
            assert anterior.fecha_hora_fin <= siguiente.fecha_hora_inicio

    # El corte de un día pasado cuadra con sus tickets (RF-13)
    corte = corte_de_caja(habiles[0])
    assert corte["totales"]["neto"] == Decimal("3200.00")
    assert corte["tickets"]["pagados"] == 8


def test_S5_03_el_historial_no_cambia_los_escenarios_de_hoy():
    hoy = timezone.localdate()
    call_command("cargar_datos_prueba", mascotas=30)
    antes = _escenarios_de_hoy(hoy)

    call_command("cargar_datos_prueba", mascotas=30, historial=12)

    assert Cita.objects.filter(motivo=MOTIVO).exists()
    assert _escenarios_de_hoy(hoy) == antes
    # El siguiente ticket de hoy sigue siendo el que esperan los guiones (D-20, D-22)
    assert siguiente_folio(hoy) == f"T-{hoy:%Y}-00003"
    assert Venta.objects.filter(folio_ticket__startswith="T-").count() == 2
    # Los clientes de los escenarios no reciben historial
    assert not Cita.objects.filter(motivo=MOTIVO, mascota__cliente__telefono__startswith="833999").exists()


def test_S5_03_sin_mascotas_no_hay_historial_y_no_falla():
    call_command("cargar_datos_prueba", mascotas=0, historial=5)
    assert not Cita.objects.filter(motivo=MOTIVO).exists()
    assert Pago.objects.filter(venta__folio_ticket__startswith="H-").count() == 0
