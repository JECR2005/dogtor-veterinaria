"""TI-12 · Ventas (Tabla 4.13): corte de caja con pagos en efectivo, tarjeta y transferencia, y una
devolución.

Criterio: el corte coincide con la suma de pagos y devoluciones por método (RF-13). Incluye S4-14: PDF del
corte, tickets con saldo pendiente de cualquier día y su aviso en el Inicio.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from django.db.models import Sum
from django.utils import timezone
from pypdf import PdfReader

from catalogos.models import CategoriaServicio
from seguridad.models import Rol
from tests import fabricas
from ventas import services
from ventas.models import Pago, Venta
from ventas.services import Partida

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def dia_de_ventas(client, crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cliente = fabricas.paciente("Max").cliente
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)  # $400.00
    sofia = recepcion.empleado

    def ticket():
        return services.generar_ticket(cliente, sofia, [Partida(servicio=bano)])

    a, b, c, d = ticket(), ticket(), ticket(), ticket()
    services.registrar_pago(a, sofia, "Efectivo", Decimal("500"))  # $400 con $100 de cambio
    services.registrar_pago(b, sofia, "Tarjeta", Decimal("250"))  # parcial: queda $150
    services.registrar_pago(c, sofia, "Transferencia", Decimal("400"))
    services.registrar_pago(d, sofia, "Efectivo", Decimal("400"))
    services.cancelar_venta(d, admin, "Cobro duplicado")  # devolución de $400 en efectivo

    # Un ticket de ayer con su pago de ayer y un abono de hoy: solo el de hoy entra al corte
    ayer = timezone.now() - timedelta(days=1)
    e = ticket()
    Venta.objects.filter(pk=e.pk).update(fecha_hora=ayer)
    # El abono de ayer se crea con su fecha: los pagos no se modifican después (TR_pago_inmutable, D-21)
    Pago.objects.create(venta=e, empleado=sofia, tipo="Abono", metodo="Tarjeta", monto=100, fecha_hora=ayer)
    Venta.objects.filter(pk=e.pk).update(saldo=Decimal("300.00"))
    services.registrar_pago(e, sofia, "Transferencia", Decimal("50"))
    client.force_login(recepcion)
    return client


def test_TI12_el_corte_coincide_con_pagos_y_devoluciones_por_metodo(dia_de_ventas):
    client = dia_de_ventas
    corte = services.corte_de_caja(HOY)
    por_metodo = {fila["metodo"]: fila for fila in corte["metodos"]}
    assert (por_metodo["Efectivo"]["abonos"], por_metodo["Efectivo"]["devoluciones"]) == (
        Decimal("800.00"),
        Decimal("400.00"),
    )
    assert (por_metodo["Efectivo"]["recibido"], por_metodo["Efectivo"]["cambio"]) == (
        Decimal("900"),
        Decimal("100"),
    )
    assert {m: f["neto"] for m, f in por_metodo.items()} == {
        "Efectivo": Decimal("400.00"),
        "Tarjeta": Decimal("250.00"),
        "Transferencia": Decimal("450.00"),
    }
    assert corte["totales"]["neto"] == Decimal("1100.00")

    # Contra la base: la suma de los pagos de hoy, por método y tipo
    inicio = timezone.make_aware(datetime.combine(HOY, time.min))
    de_hoy = Pago.objects.filter(fecha_hora__gte=inicio)
    for metodo, fila in por_metodo.items():
        abonos = de_hoy.filter(metodo=metodo, tipo="Abono").aggregate(s=Sum("monto"))["s"] or 0
        devoluciones = de_hoy.filter(metodo=metodo, tipo="Devolución").aggregate(s=Sum("monto"))["s"] or 0
        assert fila["neto"] == abonos - devoluciones, metodo

    pantalla = client.get("/ventas/corte/").content.decode()
    assert "Corte de caja" in pantalla and "data-total-neto>$1,100.00<" in pantalla
    assert "Recibido $900.00 · cambio entregado $100.00" in pantalla
    assert corte["tickets"] == {
        "generados": 4,
        "pagados": 2,
        "pendientes": 1,
        "cancelados": 1,
        "vendido": Decimal("1200.00"),
    }


def test_S4_14_pdf_del_corte_y_tickets_con_saldo(dia_de_ventas):
    client = dia_de_ventas
    respuesta = client.get(f"/ventas/corte/pdf/?fecha={HOY:%Y-%m-%d}")
    assert respuesta["Content-Type"] == "application/pdf"
    pagina = PdfReader(BytesIO(respuesta.content)).pages[0]
    assert "Corte de caja del" in pagina.extract_text() and "$1,100.00" in pagina.extract_text()
    assert (round(float(pagina.mediabox.width)), round(float(pagina.mediabox.height))) == (612, 792)

    # Pendientes de cualquier día: el de tarjeta parcial de hoy ($150) y el de ayer ($250)
    inicio = client.get("/").content.decode()
    assert 'data-aviso="tickets_con_saldo">2<' in inicio and "Por cobrar: $400.00" in inicio
    lista = client.get("/ventas/?pendientes=1").content.decode()
    assert "Tickets con saldo pendiente de cualquier día: <strong>2</strong> por $400.00" in lista


def test_S4_13_un_dia_sin_movimientos(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    pantalla = client.get("/ventas/corte/?fecha=2026-01-05").content.decode()
    assert "No hubo pagos ni devoluciones ese día." in pantalla and "data-total-neto>$0.00<" in pantalla
