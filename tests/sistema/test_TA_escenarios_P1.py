"""Escenarios de aceptación de P1 automatizados (TA-01 y TA-02, Tabla 4.14).

Recorren por las pantallas, paso a paso, el guion docs/gestion/guion_aceptacion_P1.md, igual que lo haría la
Recepcionista con el navegador (formularios, botones y mensajes), sobre la base real de pruebas.

Sirven de regresión: si un cambio rompe el flujo del guion, la CI lo detecta antes de la evaluación.
NO sustituyen la aceptación: el documento exige que la evalúe el personal de la clínica, sin ayuda del
equipo de desarrollo, con una calificación de al menos 4 de 5 (apartado 4.5.2.3, Tabla 3.20).
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import (
    CategoriaServicio,
    Cliente,
    Especie,
    Mascota,
    PreferenciaContacto,
    Puesto,
    Raza,
    Sexo,
)
from clinico.models import ExpedienteClinico
from seguridad.models import Rol
from tests import fabricas
from tests.fabricas import LUNES, en

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]


@pytest.fixture
def clinica(crear_usuario):
    """Lo que el observador prepara antes de empezar: personal con horario, servicios, razas y cuentas."""
    perro, _ = Especie.objects.get_or_create(nombre="Perro")
    Raza.objects.get_or_create(especie=perro, nombre="Labrador Retriever")
    return {
        "laura": fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura"),
        "pedro": fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro"),
        "consulta": fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30),
        "labrador": Raza.objects.get(nombre="Labrador Retriever"),
        "recepcion": crear_usuario("recepcion", rol=Rol.RECEPCIONISTA),
        "admin": crear_usuario("admin", rol=Rol.ADMINISTRADOR),
    }


def _pagina(respuesta):
    return respuesta.content.decode()


def _agendar(client, mascota, empleado, servicio, hora, seguir=True):
    datos = {"servicio": servicio.pk, "empleado": empleado.pk, "fecha": LUNES.isoformat(), "hora": hora}
    return client.post(f"/agenda/nueva/?mascota={mascota.pk}", datos, follow=seguir)


def _registrar_luna(client, clinica):
    """TA-01, pasos 1 a 3: cliente con aviso de privacidad y su perra con alergias."""
    cliente = {
        "nombre": "Mariana",
        "apellido_paterno": "Ruiz",
        "apellido_materno": "Prueba",
        "telefono": "833 555 0101",
        "preferencia_contacto": PreferenciaContacto.WHATSAPP,
    }
    paso1 = client.post("/clientes/nuevo/", cliente)
    assert "Sin la aceptación del aviso de privacidad no se puede registrar al cliente." in _pagina(paso1)
    assert not Cliente.objects.filter(nombre="Mariana").exists()

    paso2 = client.post("/clientes/nuevo/", {**cliente, "acepto_aviso_privacidad": "on"}, follow=True)
    mariana = Cliente.objects.get(nombre="Mariana")
    assert paso2.redirect_chain[-1][0] == f"/clientes/{mariana.pk}/" and "registrado" in _pagina(paso2)

    nacimiento = (timezone.localdate() - timedelta(days=3 * 365)).isoformat()
    luna = {
        "nombre": "Luna",
        "raza": clinica["labrador"].pk,
        "sexo": Sexo.HEMBRA,
        "fecha_nacimiento": nacimiento,
        "peso_actual": "22",
        "alergias": "Penicilina",
    }
    paso3 = client.post(f"/clientes/{mariana.pk}/mascotas/nueva/", luna, follow=True)
    mascota = Mascota.objects.get(nombre="Luna")
    assert mascota.cliente == mariana
    assert ExpedienteClinico.objects.get(mascota=mascota).fecha_apertura == timezone.localdate()
    assert "Alergias:" in _pagina(paso3) and "Penicilina" in _pagina(paso3)
    return mariana, mascota


def test_TA01_escenario_alta_agendar_reprogramar_y_cancelar(client, clinica):
    client.force_login(clinica["recepcion"])
    mariana, luna = _registrar_luna(client, clinica)

    # Paso 4: agendar a las 10:00
    paso4 = _agendar(client, luna, clinica["laura"], clinica["consulta"], "10:00")
    cita = Cita.objects.get(mascota=luna)
    assert "Cita agendada" in _pagina(paso4) and cita.estado == EstadoCita.PROGRAMADA
    assert timezone.localtime(cita.fecha_hora_fin) == en("10:30")

    # Paso 5: reprogramar a las 12:00; las 10:00 quedan libres
    datos = {"empleado": clinica["laura"].pk, "fecha": LUNES.isoformat(), "hora": "12:00"}
    paso5 = client.post(f"/agenda/citas/{cita.pk}/reprogramar/", datos, follow=True)
    assert "Cita reprogramada" in _pagina(paso5)
    otra = fabricas.mascota("Firulais", "Ana")
    assert "Cita agendada" in _pagina(_agendar(client, otra, clinica["laura"], clinica["consulta"], "10:00"))

    # Paso 6: búsqueda global por los últimos dígitos del teléfono
    assert "Mariana" in _pagina(client.get("/clientes/", {"q": "0101"}))

    # Paso 7: cancelar sin motivo (no deja) y con motivo
    sin_motivo = client.post(f"/agenda/citas/{cita.pk}/cancelar/", {"motivo": ""}, follow=True)
    assert "Escriba el motivo" in _pagina(sin_motivo)
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.PROGRAMADA
    paso7 = client.post(
        f"/agenda/citas/{cita.pk}/cancelar/", {"motivo": "El cliente salió de viaje"}, follow=True
    )
    assert "El espacio quedó libre" in _pagina(paso7)
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.CANCELADA

    # Paso 8: el Administrador la ve cancelada en el calendario y solo consulta
    client.logout()
    client.force_login(clinica["admin"])
    rango = {
        "start": f"{LUNES}T00:00:00-06:00",
        "end": f"{LUNES + timedelta(days=1)}T00:00:00-06:00",
        "canceladas": "1",
    }
    eventos = client.get("/agenda/eventos/", rango).json()
    assert any(
        e["title"] == "Luna · Consulta general" and e["extendedProps"]["estado"] == "Cancelada"
        for e in eventos
    )
    assert client.get("/agenda/nueva/").status_code == 403
    assert "Cancelar cita" not in _pagina(client.get(f"/agenda/citas/{cita.pk}/"))


def test_TA02_escenario_rechazos_de_horario_y_empalme(client, clinica):
    client.force_login(clinica["recepcion"])
    _, luna = _registrar_luna(client, clinica)
    firulais = fabricas.mascota("Firulais", "Ana")

    # Paso 1: Luna a las 10:00
    assert "Cita agendada" in _pagina(_agendar(client, luna, clinica["laura"], clinica["consulta"], "10:00"))

    # Paso 2: otra mascota con el mismo veterinario a las 10:15 → Empalme de horario
    paso2 = _pagina(_agendar(client, firulais, clinica["laura"], clinica["consulta"], "10:15", seguir=False))
    assert "<strong>Empalme de horario</strong>" in paso2 and "No se guardó la cita." in paso2
    assert "Elija otra hora u otro empleado, o reprograme la cita existente." in paso2

    # Paso 3: a las 10:30 sí (terminar justo cuando la otra empieza no es empalme)
    assert "Cita agendada" in _pagina(
        _agendar(client, firulais, clinica["laura"], clinica["consulta"], "10:30")
    )

    # Paso 4: 15 minutos antes del fin de la jornada (19:00) → Fuera de horario laboral
    paso4 = _pagina(_agendar(client, firulais, clinica["laura"], clinica["consulta"], "18:45", seguir=False))
    assert "<strong>Fuera de horario laboral</strong>" in paso4 and "No se guardó la cita." in paso4

    # Paso 5: Luna otra vez a las 10:00 con otro veterinario → la mascota ya tiene cita (D-16)
    paso5 = _pagina(_agendar(client, luna, clinica["pedro"], clinica["consulta"], "10:00", seguir=False))
    assert "La mascota ya tiene una cita a esa hora" in paso5

    assert Cita.objects.filter(estado=EstadoCita.PROGRAMADA).count() == 2  # solo las dos válidas
