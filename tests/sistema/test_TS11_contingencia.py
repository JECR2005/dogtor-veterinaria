"""TS-11 · Contingencia sin internet (Tabla 4.15, R07): atender con la agenda impresa y recapturar al volver.

Criterio: la atención continúa y la recaptura no pierde datos.

1. La agenda del día sale en PDF (pantalla y tarea de cada mañana) con lo necesario para atender sin sistema:
   hora, mascota, alergias, cliente, teléfono, servicio, quién atiende y casillas para anotar.
2. Con lo anotado en papel, al volver el servicio se recaptura el mismo día: consultas con aplicación y firma,
   atención de estética y cobros desde «Por cobrar hoy». Todo queda registrado y el corte cuadra.
"""

from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.management import call_command
from django.utils import timezone
from pypdf import PdfReader

from agenda.models import Cita
from catalogos.models import CategoriaProducto, CategoriaServicio, Puesto
from clinico import services as clinico
from clinico.models import Consulta, RegistroEstetica
from seguridad.models import BitacoraAuditoria, Rol
from tests import fabricas
from ventas import services as ventas
from ventas.models import Venta

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]


@pytest.fixture
def dia_con_citas():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    max_ = fabricas.paciente("Max", alergias="Penicilina")
    rocky = fabricas.paciente("Rocky")
    canela = fabricas.paciente("Canela")
    toby = fabricas.paciente("Toby")
    citas = {
        "max": fabricas.cita_de_hoy(max_, laura, consulta, "10:00"),
        "rocky": fabricas.cita_de_hoy(rocky, laura, consulta, "11:00"),
        "canela": fabricas.cita_de_hoy(canela, mario, bano, "12:00"),
        "toby": fabricas.cita_de_hoy(toby, laura, consulta, "13:00", estado="Cancelada"),
    }
    return laura, mario, citas


def _texto(pdf):
    lector = PdfReader(BytesIO(pdf))
    pagina = lector.pages[0]
    return " ".join(p.extract_text() for p in lector.pages), (
        float(pagina.mediabox.width),
        float(pagina.mediabox.height),
    )


def test_TS11_la_agenda_impresa_trae_lo_necesario_para_atender_sin_sistema(
    client, crear_usuario, dia_con_citas, tmp_path
):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert "Imprimir agenda (contingencia)" in client.get("/agenda/dia/").content.decode()
    respuesta = client.get("/agenda/dia/pdf/")
    assert respuesta["Content-Type"] == "application/pdf"
    texto, tamano = _texto(respuesta.content)
    assert tamano == (792.0, 612.0)  # carta horizontal
    for dato in ("Max", "Rocky", "Canela", "Alergias: Penicilina", "8331234567", "Consulta general", "Baño"):
        assert dato in texto, dato
    assert "Toby" not in texto  # las canceladas no se imprimen
    assert "recapture" in texto

    # La tarea de cada mañana deja el mismo PDF en la laptop, sin necesitar el servidor para imprimirlo
    call_command("generar_agenda", salida=str(tmp_path))
    (archivo,) = tmp_path.glob("Agenda-*.pdf")
    assert "Alergias: Penicilina" in _texto(archivo.read_bytes())[0]


def test_TS11_la_recaptura_al_volver_el_servicio_no_pierde_datos(dia_con_citas):
    laura, mario, citas = dia_con_citas
    sofia = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Sofía")
    vacuna = fabricas.producto("VAC-TS11", "Vacuna", stock_minimo=0, categoria=CategoriaProducto.VACUNA)
    fabricas.lote(vacuna, 10, 300)
    antes = BitacoraAuditoria.objects.count()

    # Lo anotado en la hoja: Max y Rocky atendidos (Max con vacuna), Canela bañada; todo cobrado
    for nombre in ("max", "rocky"):
        datos = {"sintomas": "Revisión", "peso_kg": Decimal("10"), "diagnostico": "Sano"}
        consulta = clinico.abrir_consulta(citas[nombre], laura, datos)
        if nombre == "max":
            proxima = timezone.localdate() + timedelta(days=365)
            clinico.registrar_aplicacion(consulta, laura, vacuna, 1, "1 mL", proxima)
        clinico.firmar(consulta, laura)
    clinico.registrar_estetica(citas["canela"], mario, {"estado_pelaje_piel": "Sano"})
    por_cobrar = list(ventas.citas_por_cobrar())
    assert {c.pk for c in por_cobrar} == {citas["max"].pk, citas["rocky"].pk, citas["canela"].pk}
    for cita, metodo in zip(por_cobrar, ["Efectivo", "Tarjeta", "Transferencia"], strict=True):
        venta = ventas.generar_ticket(
            cita.mascota.cliente, sofia, ventas.partidas_de_la_cita(cita), cita=cita
        )
        ventas.registrar_pago(venta, sofia, metodo, venta.total, referencia="Recaptura")

    # Nada se perdió: cada cita quedó completada, con su registro y su ticket pagado; el corte cuadra
    vigentes = Cita.objects.exclude(estado="Cancelada")
    assert set(vigentes.values_list("estado", flat=True)) == {"Completada"}
    assert Consulta.objects.filter(estado="Firmada").count() == 2 and RegistroEstetica.objects.count() == 1
    tickets = Venta.objects.filter(cita__in=vigentes)
    assert tickets.count() == 3 and set(tickets.values_list("estado", flat=True)) == {"Pagada"}
    assert not list(ventas.citas_por_cobrar())
    corte = ventas.corte_de_caja()
    assert corte["totales"]["neto"] == sum(t.total for t in tickets)
    assert BitacoraAuditoria.objects.count() > antes  # la recaptura también queda en la bitácora
