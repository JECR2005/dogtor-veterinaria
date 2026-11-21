"""TI-11 · Estética y Expediente clínico (Tabla 4.13): el estilista registra un hallazgo y avisa.

Criterio: el aviso aparece en la pantalla del veterinario (su Inicio y la consulta de la mascota) y el
registro en el historial clínico (RF-10). La cita de estética queda Completada al guardar.
"""

import pytest

from agenda.models import EstadoCita
from catalogos.models import CategoriaServicio, Puesto
from clinico.models import Consulta, RegistroEstetica
from seguridad.models import Rol, Usuario
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HALLAZGO = "Zona sin pelo con costras en el lomo"


@pytest.fixture
def escenario():
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    fabricas.cuenta(mario, "mario", rol=Rol.ESTILISTA)
    fabricas.cuenta(laura, "laura", rol=Rol.VETERINARIO)
    canela = fabricas.paciente("Canela")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    cita = fabricas.cita_de_hoy(canela, mario, bano, "12:00")
    return mario, laura, canela, cita


def _entrar(client, usuario):
    client.force_login(Usuario.objects.get(nombre_usuario=usuario))


def test_TI11_el_estilista_avisa_y_el_veterinario_lo_ve(client, escenario):
    _, laura, canela, cita = escenario
    _entrar(client, "mario")
    agenda = client.get("/estetica/").content.decode()
    assert "Mi agenda de estética" in agenda and "Canela" in agenda
    assert f"/estetica/citas/{cita.pk}/atender/" in agenda
    assert 'data-aviso="por_registrar">1<' in client.get("/").content.decode()

    datos = {"estado_pelaje_piel": "Pelaje opaco", "hallazgos": HALLAZGO, "aviso_veterinario": "on"}
    respuesta = client.post(f"/estetica/citas/{cita.pk}/atender/", datos, follow=True)
    contenido = respuesta.content.decode()
    assert "la cita quedó completada. Se avisó al veterinario." in contenido
    assert "Ver registro" in contenido and "Se avisó al veterinario" in contenido
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.COMPLETADA
    registro = RegistroEstetica.objects.get()
    assert registro.aviso_veterinario and registro.hallazgos == HALLAZGO

    # El veterinario lo ve en su Inicio…
    _entrar(client, "laura")
    inicio = client.get("/").content.decode()
    assert 'data-aviso="estetica">1<' in inicio and HALLAZGO in inicio and "Mario Prueba" in inicio
    # …en el historial clínico…
    historial = client.get(f"/clinica/mascotas/{canela.pk}/historial/").content.decode()
    assert "Aviso al veterinario" in historial and f"Hallazgos: {HALLAZGO}" in historial
    # …y junto a las alergias al atender a la mascota
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    revision = fabricas.cita_de_hoy(canela, laura, consulta, "18:00")
    atender = client.get(f"/clinica/citas/{revision.pk}/atender/").content.decode()
    assert 'data-alerta="aviso-estetica"' in atender and HALLAZGO in atender

    client.post(f"/clinica/citas/{revision.pk}/atender/", {"sintomas": "Revisión de piel", "peso_kg": "12"})
    assert Consulta.objects.count() == 1
    consulta_abierta = client.get(f"/clinica/consultas/{Consulta.objects.get().pk}/").content.decode()
    assert HALLAZGO in consulta_abierta
    assert 'data-aviso="estetica">0<' in client.get("/").content.decode()  # ya pasó a consulta


def test_TI11_sin_hallazgo_no_hay_aviso_y_la_cita_sigue_programada(client, escenario):
    _, _, _, cita = escenario
    _entrar(client, "mario")
    datos = {"estado_pelaje_piel": "Bien", "hallazgos": "", "aviso_veterinario": "on"}
    contenido = client.post(f"/estetica/citas/{cita.pk}/atender/", datos).content.decode()
    assert "Para avisar al veterinario, describa el hallazgo." in contenido
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.PROGRAMADA and not RegistroEstetica.objects.exists()


def test_TI11_otro_estilista_no_la_registra_y_el_veterinario_solo_consulta(client, escenario, crear_usuario):
    _, _, _, cita = escenario
    client.force_login(crear_usuario("sofia", rol=Rol.ESTILISTA))
    assert client.get(f"/estetica/citas/{cita.pk}/atender/").status_code == 404
    assert "Registrar atención" not in client.get("/estetica/").content.decode()  # no es su agenda

    _entrar(client, "laura")
    agenda = client.get("/estetica/").content.decode()
    assert "Agenda de estética" in agenda and "Canela" in agenda and "Registrar atención" not in agenda
    datos = {"estado_pelaje_piel": "Bien"}
    assert client.post(f"/estetica/citas/{cita.pk}/atender/", datos).status_code == 403
    assert not RegistroEstetica.objects.exists()


def test_TI11_el_registro_se_consulta_en_solo_lectura(client, escenario, crear_usuario):
    mario, _, _, cita = escenario
    _entrar(client, "mario")
    client.post(f"/estetica/citas/{cita.pk}/atender/", {"estado_pelaje_piel": "Pelaje sano"})
    registro = RegistroEstetica.objects.get()
    # Volver a «Registrar atención» lleva al registro, no a otro formulario
    respuesta = client.get(f"/estetica/citas/{cita.pk}/atender/")
    assert respuesta.status_code == 302 and respuesta.url == f"/estetica/registros/{registro.pk}/"

    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    contenido = client.get(f"/estetica/registros/{registro.pk}/").content.decode()
    assert "Pelaje sano" in contenido and "Hallazgos" in contenido and "Ninguno" in contenido
