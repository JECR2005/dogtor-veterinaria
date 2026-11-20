"""TI-10 · Recordatorios y Agenda (Tabla 4.13): contactar al cliente y agendar la siguiente dosis (S3-11).

Criterio: desde la lista del día, «Contactado y agendar» deja el recordatorio Contactado (con quién y cuándo)
y abre la nueva cita con la mascota, la fecha de la dosis y el servicio de Vacunación ya elegidos. La cita
respeta las reglas de la agenda: horario laboral y sin empalmes (RF-05, RF-09).
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from agenda import services as agenda
from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, PreferenciaContacto, Puesto
from recordatorios.models import EstadoRecordatorio, Recordatorio
from seguridad.models import Rol
from tests import fabricas
from tests.fabricas import en

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()
# La próxima dosis cae en los próximos 3 días, pero no en domingo (no hay servicio, RNF-06)
DIAS = next(d for d in (3, 2, 1) if (HOY + timedelta(days=d)).isoweekday() != 7)
PROXIMA = HOY + timedelta(days=DIAS)


@pytest.fixture
def escenario(client, crear_usuario):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    vacunacion = fabricas.servicio("Vacunación", CategoriaServicio.VACUNACION, 20)
    michi = fabricas.paciente("Michi")
    michi.cliente.nombre, michi.cliente.preferencia_contacto = "Jorge", PreferenciaContacto.WHATSAPP
    michi.cliente.save()
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    fabricas.aplicacion(michi, laura, vacuna, DIAS)
    usuario = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    client.force_login(usuario)
    return client, usuario, laura, vacunacion, michi


def test_TI10_la_lista_muestra_al_cliente_con_su_canal(escenario):
    client, _, _, _, michi = escenario
    lista = client.get("/recordatorios/").content.decode()
    assert Recordatorio.objects.count() == 1  # se generó al abrir la lista
    assert "Próxima dosis: Vacuna antirrábica" in lista and "Michi" in lista
    assert f"https://wa.me/52{michi.cliente.telefono}?text=" in lista and "Abrir WhatsApp" in lista
    assert 'data-aviso="pendientes">1<' in lista
    assert 'data-aviso="recordatorios">1<' in client.get("/").content.decode()  # contador del Inicio


def test_TI10_contactar_y_agendar_la_siguiente_dosis(escenario):
    client, usuario, laura, vacunacion, michi = escenario
    client.get("/recordatorios/")
    recordatorio = Recordatorio.objects.get()

    respuesta = client.post(f"/recordatorios/{recordatorio.pk}/resultado/", {"accion": "agendar"})
    esperado = f"/agenda/nueva/?mascota={michi.pk}&fecha={PROXIMA.isoformat()}&servicio={vacunacion.pk}"
    assert respuesta.status_code == 302 and respuesta.url == esperado
    recordatorio.refresh_from_db()
    assert recordatorio.estado == EstadoRecordatorio.CONTACTADO
    assert recordatorio.empleado == usuario.empleado and recordatorio.fecha_contacto is not None

    formulario = client.get(esperado).content.decode()
    assert "Michi" in formulario and PROXIMA.isoformat() in formulario

    # La agenda sigue mandando: con Laura ocupada a las 10:00, rechaza el empalme y acepta las 10:30
    otra = fabricas.mascota("Canela")
    agenda.agendar(otra, laura, vacunacion, en("10:00", PROXIMA))
    datos = {"servicio": vacunacion.pk, "empleado": laura.pk, "fecha": PROXIMA.isoformat(), "hora": "10:00"}
    assert "Empalme de horario" in client.post(esperado, datos).content.decode()
    datos["hora"] = "10:30"
    respuesta = client.post(esperado, {**datos, "motivo": "Segunda dosis"}, follow=True)
    assert "Cita agendada" in respuesta.content.decode()
    cita = Cita.objects.get(mascota=michi, fecha_hora_inicio=en("10:30", PROXIMA))
    assert cita.estado == EstadoCita.PROGRAMADA and cita.servicio == vacunacion

    # Ya no está por contactar; aparece en «Contactados hoy»
    lista = client.get("/recordatorios/").content.decode()
    assert 'data-aviso="pendientes">0<' in lista and "No hay clientes por contactar." in lista


def test_TI10_sin_respuesta_queda_para_reintentar_y_luego_contactado(escenario):
    client, *_ = escenario
    client.get("/recordatorios/")
    recordatorio = Recordatorio.objects.get()
    direccion = f"/recordatorios/{recordatorio.pk}/resultado/"
    contenido = client.post(direccion, {"accion": "sin_respuesta"}, follow=True).content.decode()
    assert "sin respuesta; puede volver a intentarlo" in contenido
    assert "Sin respuesta: volver a intentar" in contenido
    client.post(f"/recordatorios/{recordatorio.pk}/resultado/", {"accion": "contactado"})
    recordatorio.refresh_from_db()
    assert recordatorio.estado == EstadoRecordatorio.CONTACTADO


def test_TI10_el_administrador_consulta_sin_botones(escenario, client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    lista = client.get("/recordatorios/").content.decode()
    assert "Michi" in lista and "Contactado y agendar" not in lista
    recordatorio = Recordatorio.objects.get()
    respuesta = client.post(f"/recordatorios/{recordatorio.pk}/resultado/", {"accion": "contactado"})
    assert respuesta.status_code == 403
    recordatorio.refresh_from_db()
    assert recordatorio.estado == EstadoRecordatorio.PENDIENTE
