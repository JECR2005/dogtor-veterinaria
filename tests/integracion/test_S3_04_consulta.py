"""S3-04 a S3-06 · UI-11 Consulta clínica y UI-14 Historial por las pantallas (RF-06, RD-01, RD-07, D-17)."""

from decimal import Decimal

import pytest

from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.models import Consulta
from seguridad.models import Rol, Usuario
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def clinica():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    pedro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    general = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    max_ = fabricas.paciente("Max", alergias="Penicilina")
    luna = fabricas.paciente("Luna")
    return {
        "laura": laura,
        "pedro": pedro,
        "cita_laura": fabricas.cita_de_hoy(max_, laura, general, "10:00"),
        "cita_pedro": fabricas.cita_de_hoy(luna, pedro, general, "11:00"),
        "max": max_,
    }


def _entrar(client, empleado, rol=Rol.VETERINARIO):
    usuario = Usuario.objects.create_user(f"u{empleado.pk}", "Clave-Prueba-2026", empleado=empleado, rol=rol)
    client.force_login(usuario)
    return client


def test_S3_04_el_veterinario_ve_sus_consultas_del_dia_y_el_administrador_todas(
    client, clinica, crear_usuario
):
    contenido = _entrar(client, clinica["laura"]).get("/clinica/").content.decode()
    assert "Mis consultas de hoy" in contenido and "Max" in contenido and "Luna" not in contenido
    assert "Alergias" in contenido and f"/clinica/citas/{clinica['cita_laura'].pk}/atender/" in contenido
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    contenido = client.get("/clinica/").content.decode()
    assert "Max" in contenido and "Luna" in contenido and "/atender/" not in contenido  # ○ solo consulta


def test_S3_04_atender_muestra_la_alerta_de_alergias_y_pide_sintomas_y_peso(client, clinica):
    _entrar(client, clinica["laura"])
    url = f"/clinica/citas/{clinica['cita_laura'].pk}/atender/"
    pantalla = client.get(url).content.decode()
    assert 'data-alerta="alergias"' in pantalla and "Penicilina" in pantalla
    contenido = client.post(url, {"sintomas": "", "peso_kg": ""}).content.decode()
    assert "Este campo es obligatorio." in contenido and not Consulta.objects.exists()
    respuesta = client.post(url, {"sintomas": "Cojera", "peso_kg": "28.5"}, follow=True)
    assert "Consulta de Max abierta." in respuesta.content.decode()
    assert client.get(url).url == f"/clinica/consultas/{Consulta.objects.get().pk}/"  # ya abierta: redirige


def test_S3_04_un_veterinario_no_atiende_la_cita_de_otro(client, clinica):
    _entrar(client, clinica["pedro"])
    assert client.get(f"/clinica/citas/{clinica['cita_laura'].pk}/atender/").status_code == 404


def test_S3_04_la_cita_ofrece_atender_al_veterinario_asignado(client, clinica):
    _entrar(client, clinica["laura"])
    assert "Atender consulta" in client.get(f"/agenda/citas/{clinica['cita_laura'].pk}/").content.decode()


def test_S3_05_guardar_y_firmada_queda_en_solo_lectura(client, clinica):
    _entrar(client, clinica["laura"])
    consulta = services.abrir_consulta(
        clinica["cita_laura"], clinica["laura"], {"sintomas": "Tos", "peso_kg": Decimal("28")}
    )
    url = f"/clinica/consultas/{consulta.pk}/"
    datos = {"sintomas": "Tos seca", "peso_kg": "28.20", "diagnostico": "Traqueobronquitis"}
    assert "Consulta guardada." in client.post(url, datos, follow=True).content.decode()
    assert "Firmar consulta" in client.get(url).content.decode()
    client.post(f"{url}firmar/")
    pantalla = client.get(url).content.decode()
    assert "data-solo-lectura" in pantalla and "Es de solo lectura (RD-07)" in pantalla
    assert 'name="diagnostico"' not in pantalla  # ya no hay campos para escribir
    respuesta = client.post(url, {**datos, "diagnostico": "Cambio"}, follow=True)
    assert "solo lectura" in respuesta.content.decode()
    assert Consulta.objects.get(pk=consulta.pk).diagnostico == "Traqueobronquitis"


def test_S3_05_el_administrador_ve_la_consulta_pero_no_la_edita_ni_firma(client, clinica, crear_usuario):
    consulta = services.abrir_consulta(
        clinica["cita_laura"], clinica["laura"], {"sintomas": "Tos", "peso_kg": Decimal("28")}
    )
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    pantalla = client.get(f"/clinica/consultas/{consulta.pk}/").content.decode()
    assert "Tos" in pantalla and 'name="sintomas"' not in pantalla and "Firmar consulta" not in pantalla
    assert client.post(f"/clinica/consultas/{consulta.pk}/firmar/").status_code == 403


def test_S3_06_historial_clinico_en_orden_y_enlazado_desde_la_mascota(client, clinica, crear_usuario):
    laura = clinica["laura"]
    consulta = services.abrir_consulta(
        clinica["cita_laura"], laura, {"sintomas": "Tos", "peso_kg": Decimal("28"), "diagnostico": "Sano"}
    )
    services.firmar(consulta, laura)
    _entrar(client, laura)
    historial = client.get(f"/clinica/mascotas/{clinica['max'].pk}/historial/").content.decode()
    assert "Historial clínico de Max" in historial and "Sano" in historial and "Firmada" in historial
    assert "Historial clínico" in client.get(f"/clientes/mascotas/{clinica['max'].pk}/").content.decode()
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert (
        f"/clinica/mascotas/{clinica['max'].pk}/historial/"
        not in client.get(f"/clientes/mascotas/{clinica['max'].pk}/").content.decode()
    )
    assert client.get(f"/clinica/mascotas/{clinica['max'].pk}/historial/").status_code == 403
