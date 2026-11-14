"""S1-13 · Agendar, reprogramar, cancelar con motivo y completar (RF-05, UI-07).

Criterio del plan: al cancelar o reprogramar, el espacio se libera de inmediato.
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


# --- Servicios ---------------------------------------------------------------------
def test_S1_13_cancelar_libera_el_espacio_de_inmediato(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="Empalme de horario"):
        services.agendar(mascota, veterinario, consulta, en("10:00"))
    services.cancelar(cita, "  El cliente   pidió otro día ")
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.CANCELADA and cita.motivo_cancelacion == "El cliente pidió otro día"
    assert services.agendar(mascota, veterinario, consulta, en("10:00"))  # el espacio ya está libre


@pytest.mark.parametrize("motivo", ["", "   ", None])
def test_cancelar_exige_motivo(mascota, veterinario, consulta, motivo):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="motivo"):
        services.cancelar(cita, motivo)
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.PROGRAMADA


def test_S1_13_reprogramar_libera_el_espacio_anterior(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    services.reprogramar(cita, en("12:00"))
    cita.refresh_from_db()
    assert timezone.localtime(cita.fecha_hora_inicio) == en("12:00")
    assert timezone.localtime(cita.fecha_hora_fin) == en("12:30")
    otra = fabricas.mascota("Michi", "Bruno")
    assert services.agendar(otra, veterinario, consulta, en("10:00"))  # el espacio anterior quedó libre


def test_reprogramar_a_un_espacio_ocupado_no_cambia_nada(mascota, veterinario, consulta):
    services.agendar(fabricas.mascota("Michi", "Bruno"), veterinario, consulta, en("12:00"))
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="Empalme de horario"):
        services.reprogramar(cita, en("12:15"))
    cita.refresh_from_db()
    assert timezone.localtime(cita.fecha_hora_inicio) == en("10:00")


def test_reprogramar_unos_minutos_dentro_de_su_propio_espacio(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    services.reprogramar(cita, en("10:15"))  # se traslapa solo consigo misma
    cita.refresh_from_db()
    assert timezone.localtime(cita.fecha_hora_inicio) == en("10:15")


def test_reprogramar_con_otro_empleado_respeta_el_puesto(mascota, veterinario, estilista, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="lo presta un Veterinario"):
        services.reprogramar(cita, en("10:00"), estilista)
    otro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    services.reprogramar(cita, en("10:00"), otro)
    cita.refresh_from_db()
    assert cita.empleado == otro


def test_completar_solo_citas_que_ya_empezaron(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="todavía no empieza"):
        services.completar(cita)
    services.completar(cita, ahora=en("10:05"))
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.COMPLETADA


@pytest.mark.parametrize("estado", [EstadoCita.COMPLETADA, EstadoCita.CANCELADA])
def test_solo_se_modifican_citas_programadas(mascota, veterinario, consulta, estado):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    Cita.objects.filter(pk=cita.pk).update(estado=estado, motivo_cancelacion="Prueba")
    for accion in (
        lambda: services.cancelar(cita, "Otro motivo"),
        lambda: services.reprogramar(cita, en("12:00")),
        lambda: services.completar(cita, ahora=en("11:00")),
    ):
        with pytest.raises(services.CitaRechazada, match="Solo se modifican citas Programadas"):
            accion()


# --- Pantallas ---------------------------------------------------------------------
def test_nueva_cita_sin_mascota_pide_buscar_al_cliente(recepcion, mascota):
    contenido = recepcion.get("/agenda/nueva/").content.decode()
    assert "¿para qué mascota?" in contenido
    contenido = recepcion.get("/agenda/nueva/", {"q": "ana"}).content.decode()
    assert f"/agenda/nueva/?mascota={mascota.pk}" in contenido


def test_TI02_al_elegir_estetica_solo_aparecen_estilistas(recepcion, mascota, veterinario, estilista, bano):
    contenido = recepcion.get("/agenda/nueva/", {"mascota": mascota.pk, "servicio": bano.pk}).content.decode()
    assert "Sofía Prueba" in contenido and "Laura Prueba" not in contenido
    assert "Dura 60 minutos; lo presta un Estilista." in contenido


def test_agendar_desde_la_pantalla(recepcion, mascota, veterinario, consulta):
    datos = {
        "servicio": consulta.pk,
        "empleado": veterinario.pk,
        "fecha": LUNES.isoformat(),
        "hora": "10:00",
        "motivo": "Revisión anual",
    }
    respuesta = recepcion.post(f"/agenda/nueva/?mascota={mascota.pk}", datos, follow=True)
    cita = Cita.objects.get()
    assert respuesta.redirect_chain[-1][0] == f"/agenda/citas/{cita.pk}/"
    contenido = respuesta.content.decode()
    assert "Cita agendada" in contenido and "a las 10:00" in contenido
    assert cita.motivo == "Revisión anual" and cita.estado == EstadoCita.PROGRAMADA


@pytest.mark.parametrize(
    "hora, mensaje",
    [
        ("10:15", "Empalme de horario"),
        ("18:45", "Fuera de horario laboral"),
        ("10:10", "Use horas en bloques"),
    ],
)
def test_la_pantalla_muestra_por_que_se_rechaza(recepcion, mascota, veterinario, consulta, hora, mensaje):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    datos = {"servicio": consulta.pk, "empleado": veterinario.pk, "fecha": LUNES.isoformat(), "hora": hora}
    contenido = recepcion.post(f"/agenda/nueva/?mascota={mascota.pk}", datos).content.decode()
    assert mensaje in contenido
    assert Cita.objects.count() == 1


def test_cancelar_y_reprogramar_desde_la_pantalla(recepcion, mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    contenido = recepcion.get(f"/agenda/citas/{cita.pk}/").content.decode()
    assert "Reprogramar" in contenido and "Cancelar cita" in contenido

    datos = {"empleado": veterinario.pk, "fecha": LUNES.isoformat(), "hora": "11:00"}
    respuesta = recepcion.post(f"/agenda/citas/{cita.pk}/reprogramar/", datos, follow=True)
    assert "Cita reprogramada" in respuesta.content.decode()

    sin_motivo = recepcion.post(f"/agenda/citas/{cita.pk}/cancelar/", {"motivo": ""}, follow=True)
    assert "Escriba el motivo" in sin_motivo.content.decode()
    respuesta = recepcion.post(
        f"/agenda/citas/{cita.pk}/cancelar/", {"motivo": "Enfermó el dueño"}, follow=True
    )
    assert "El espacio quedó libre" in respuesta.content.decode()
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.CANCELADA


def test_la_agenda_del_dia_lista_las_citas_y_filtra_por_empleado(
    recepcion, mascota, veterinario, estilista, consulta
):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    contenido = recepcion.get("/agenda/dia/", {"fecha": LUNES.isoformat()}).content.decode()
    assert "10:00–10:30" in contenido and "Firulais" in contenido
    contenido = recepcion.get(
        "/agenda/dia/", {"fecha": LUNES.isoformat(), "empleado": estilista.pk}
    ).content.decode()
    assert "Firulais" not in contenido and "No hay citas" in contenido
    dia_anterior = (LUNES - timedelta(days=1)).isoformat()
    assert (
        f"fecha={dia_anterior}"
        in recepcion.get("/agenda/dia/", {"fecha": LUNES.isoformat()}).content.decode()
    )


def test_la_ficha_de_la_mascota_ofrece_agendar_y_lista_sus_citas(recepcion, mascota, veterinario, consulta):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    contenido = recepcion.get(f"/clientes/mascotas/{mascota.pk}/").content.decode()
    assert "Agendar cita" in contenido and "Citas recientes" in contenido and "Consulta general" in contenido


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.ADMINISTRADOR])
def test_los_roles_de_consulta_ven_la_agenda_pero_no_la_modifican(
    client, crear_usuario, rol, mascota, veterinario, consulta
):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    client.force_login(crear_usuario("usuario", rol=rol))
    assert client.get("/agenda/", {"fecha": LUNES.isoformat()}).status_code == 200
    detalle = client.get(f"/agenda/citas/{cita.pk}/").content.decode()
    assert "Cancelar cita" not in detalle and "Reprogramar" not in detalle
    assert "Agendar cita" not in client.get(f"/clientes/mascotas/{mascota.pk}/").content.decode()
    assert client.get("/agenda/nueva/").status_code == 403
    assert client.post(f"/agenda/citas/{cita.pk}/cancelar/", {"motivo": "x"}).status_code == 403
    assert client.post(f"/agenda/citas/{cita.pk}/completar/").status_code == 403
    assert client.get(f"/agenda/citas/{cita.pk}/reprogramar/").status_code == 403


def test_D16_la_pantalla_avisa_que_la_mascota_ya_tiene_cita(recepcion, mascota, veterinario, consulta):
    otro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Hugo")
    services.agendar(mascota, veterinario, consulta, en("17:30"))
    datos = {"servicio": consulta.pk, "empleado": otro.pk, "fecha": LUNES.isoformat(), "hora": "17:30"}
    contenido = recepcion.post(f"/agenda/nueva/?mascota={mascota.pk}", datos).content.decode()
    assert "La mascota ya tiene una cita a esa hora" in contenido and "Laura Prueba" in contenido
    assert Cita.objects.count() == 1
