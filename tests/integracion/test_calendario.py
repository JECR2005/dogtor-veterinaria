"""S1-14 · UI-07 Calendario por empleado (RF-05, D-07) y TI-02.

TI-02 (Tabla 4.13): agendar un servicio de estética. La lista de empleados muestra solo estilistas; la
duración del servicio define la hora de fin; un horario ocupado se rechaza.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from agenda import services
from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, Puesto
from seguridad.models import Rol
from tests import fabricas
from tests.fabricas import LUNES, en

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def veterinario():
    return fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")


@pytest.fixture
def estilista():
    return fabricas.empleado(Puesto.ESTILISTA, nombre="Sofía")


@pytest.fixture
def consulta():
    return fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)


@pytest.fixture
def bano():
    return fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)


@pytest.fixture
def mascota():
    return fabricas.mascota()


@pytest.fixture
def recepcion(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    return client


def _rango(dia=LUNES):
    return {
        "start": f"{dia.isoformat()}T00:00:00-06:00",
        "end": f"{(dia + timedelta(days=7)).isoformat()}T00:00:00-06:00",
    }


# --- TI-02 --------------------------------------------------------------------------
def test_TI02_agendar_estetica(recepcion, mascota, veterinario, estilista, bano):
    # 1. La lista de empleados muestra solo estilistas
    contenido = recepcion.get("/agenda/nueva/", {"mascota": mascota.pk, "servicio": bano.pk}).content.decode()
    assert "Sofía Prueba" in contenido and "Laura Prueba" not in contenido

    # 2. La duración del servicio define la hora de fin
    datos = {"servicio": bano.pk, "empleado": estilista.pk, "fecha": LUNES.isoformat(), "hora": "11:00"}
    recepcion.post(f"/agenda/nueva/?mascota={mascota.pk}", datos)
    cita = Cita.objects.get()
    assert timezone.localtime(cita.fecha_hora_fin) == en("12:00")

    # 3. Un horario ocupado se rechaza (otra mascota, misma estilista, 11:30)
    otra = fabricas.mascota("Michi", "Bruno")
    datos["hora"] = "11:30"
    contenido = recepcion.post(f"/agenda/nueva/?mascota={otra.pk}", datos).content.decode()
    assert "Empalme de horario" in contenido
    assert Cita.objects.count() == 1


# --- Calendario --------------------------------------------------------------------
def test_el_calendario_carga_fullcalendar_y_el_filtro(recepcion, veterinario, estilista):
    contenido = recepcion.get("/agenda/").content.decode()
    assert "vendor/fullcalendar/index.global.min.js" in contenido and 'id="calendario"' in contenido
    assert 'data-eventos="/agenda/eventos/"' in contenido and 'data-puede-agendar="si"' in contenido
    assert "Laura Prueba (Veterinario)" in contenido and "Sofía Prueba (Estilista)" in contenido
    assert "Nueva cita" in contenido and "Lista del día" in contenido


def test_el_menu_agenda_lleva_al_calendario(recepcion):
    assert 'href="/agenda/"' in recepcion.get("/").content.decode()


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.ADMINISTRADOR])
def test_los_roles_de_consulta_ven_el_calendario_sin_agendar(client, crear_usuario, rol):
    client.force_login(crear_usuario("usuario", rol=rol))
    contenido = client.get("/agenda/").content.decode()
    assert 'id="calendario"' in contenido
    assert 'data-puede-agendar=""' in contenido and "Nueva cita" not in contenido


def test_eventos_del_rango_en_formato_fullcalendar(recepcion, mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"), motivo="Revisión")
    eventos = recepcion.get("/agenda/eventos/", _rango()).json()
    assert eventos == [
        {
            "id": cita.pk,
            "title": "Firulais · Consulta general",
            "start": f"{LUNES.isoformat()}T10:00:00-06:00",
            "end": f"{LUNES.isoformat()}T10:30:00-06:00",
            "url": f"/agenda/citas/{cita.pk}/",
            "backgroundColor": "#0d6efd",
            "borderColor": "#0d6efd",
            "extendedProps": {
                "estado": "Programada",
                "empleado": "Laura Prueba",
                "cliente": "Ana López",
                "telefono": "8331234567",
            },
        }
    ]


def test_eventos_filtra_por_empleado_y_oculta_canceladas(
    recepcion, mascota, veterinario, estilista, consulta, bano
):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    cancelada = services.agendar(fabricas.mascota("Michi", "Bruno"), estilista, bano, en("12:00"))
    services.cancelar(cancelada, "Prueba")

    todos = recepcion.get("/agenda/eventos/", _rango()).json()
    assert [e["title"] for e in todos] == ["Firulais · Consulta general"]
    con_canceladas = recepcion.get("/agenda/eventos/", {**_rango(), "canceladas": "1"}).json()
    assert {e["extendedProps"]["estado"] for e in con_canceladas} == {
        EstadoCita.PROGRAMADA,
        EstadoCita.CANCELADA,
    }
    solo_estilista = recepcion.get(
        "/agenda/eventos/", {**_rango(), "empleado": estilista.pk, "canceladas": "1"}
    ).json()
    assert [e["title"] for e in solo_estilista] == ["Michi · Baño"]


def test_eventos_fuera_del_rango_no_aparecen(recepcion, mascota, veterinario, consulta):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    semana_siguiente = _rango(LUNES + timedelta(days=7))
    assert recepcion.get("/agenda/eventos/", semana_siguiente).json() == []


@pytest.mark.parametrize(
    "parametros", [{}, {"start": "ayer", "end": "hoy"}, {"start": "2026-11-20", "end": "2026-11-16"}]
)
def test_eventos_rechaza_un_rango_no_valido(recepcion, parametros):
    assert recepcion.get("/agenda/eventos/", parametros).status_code == 400


def test_eventos_exige_sesion(client):
    assert client.get("/agenda/eventos/", _rango()).status_code == 302


def test_clic_en_un_espacio_lleva_a_nueva_cita_con_dia_y_hora(recepcion, mascota, veterinario, consulta):
    elegir = recepcion.get(
        "/agenda/nueva/", {"fecha": LUNES.isoformat(), "hora": "10:30", "q": "ana"}
    ).content.decode()
    assert f"Espacio elegido: {LUNES.isoformat()} a las 10:30" in elegir
    assert (
        f"?mascota={mascota.pk}&" in elegir
        and f"fecha={LUNES.isoformat()}" in elegir
        and "hora=10%3A30" in elegir
    )
    formulario = recepcion.get(
        "/agenda/nueva/",
        {"mascota": mascota.pk, "servicio": consulta.pk, "fecha": LUNES.isoformat(), "hora": "10:30"},
    ).content.decode()
    assert f'value="{LUNES.isoformat()}"' in formulario and 'value="10:30"' in formulario
