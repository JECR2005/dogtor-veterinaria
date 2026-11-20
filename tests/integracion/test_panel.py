"""S1-16 · UI-02 Panel de inicio por rol con las citas del día (Tabla 4.4). Criterio: cada rol ve su panel."""

from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, Puesto
from seguridad.models import Rol, Usuario
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def hoy_a_las(hora):
    return timezone.make_aware(datetime.combine(timezone.localdate(), time.fromisoformat(hora)))


def _cita(mascota, empleado, servicio, hora, estado=EstadoCita.PROGRAMADA):
    """Citas de hoy creadas directo en la base: el panel solo las muestra (las reglas se prueban aparte)."""
    inicio = hoy_a_las(hora)
    return Cita.objects.create(
        mascota=mascota,
        empleado=empleado,
        servicio=servicio,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=inicio + timedelta(minutes=servicio.duracion_min),
        estado=estado,
        motivo_cancelacion="Prueba" if estado == EstadoCita.CANCELADA else None,
    )


@pytest.fixture
def dia():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    pedro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    sofia = fabricas.empleado(Puesto.ESTILISTA, nombre="Sofía")
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    firulais, michi = fabricas.mascota("Firulais", "Ana"), fabricas.mascota("Michi", "Bruno")
    _cita(firulais, laura, consulta, "10:00")
    _cita(michi, pedro, consulta, "11:00")
    _cita(michi, sofia, bano, "12:00")
    _cita(firulais, laura, consulta, "13:00", EstadoCita.CANCELADA)
    return {"laura": laura, "pedro": pedro, "sofia": sofia}


def _entrar_como(client, empleado, rol):
    client.force_login(
        Usuario.objects.create_user(f"u{empleado.pk}", "Clave-Prueba-2026", empleado=empleado, rol=rol)
    )
    return client.get("/").content.decode()


def test_S1_16_recepcion_ve_todas_las_citas_de_hoy_con_quien_atiende(client, crear_usuario, dia):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    panel = client.get("/").content.decode()
    assert "Citas de hoy" in panel and "Atiende" in panel
    assert "Laura Prueba" in panel and "Pedro Prueba" in panel and "Sofía Prueba" in panel
    assert 'data-aviso="citas_hoy">3<' in panel  # la cancelada no cuenta
    assert "Recordatorios pendientes" in panel and "Cuentas bloqueadas" not in panel


def test_S1_16_el_veterinario_ve_solo_sus_citas(client, dia):
    panel = _entrar_como(client, dia["laura"], Rol.VETERINARIO)
    assert "Mis citas de hoy" in panel and "Atiende" not in panel
    assert "Firulais" in panel and "Michi" not in panel  # ni la de Pedro ni la de estética
    assert 'data-aviso="citas_hoy">1<' in panel
    assert "Avisos de estética" in panel
    assert 'href="/clinica/"' in panel  # botón «Consultas del día» (UI-11, desde P3)


def test_S1_16_el_estilista_ve_solo_sus_citas(client, dia):
    panel = _entrar_como(client, dia["sofia"], Rol.ESTILISTA)
    assert "Mis citas de hoy" in panel and "Baño" in panel and "Consulta general" not in panel
    assert "Avisos de estética" not in panel and "Recordatorios pendientes" not in panel


def test_S1_16_el_administrador_ve_todo_y_sus_avisos(client, crear_usuario, dia):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    panel = client.get("/").content.decode()
    assert "Citas de hoy" in panel and "Sofía Prueba" in panel
    assert "Cuentas bloqueadas" in panel and "Alertas de inventario" in panel


def test_sin_citas_el_panel_lo_dice(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    panel = client.get("/").content.decode()
    assert "No hay citas hoy." in panel and 'data-aviso="citas_hoy">0<' in panel


def test_la_proxima_cita_del_dia(client, crear_usuario, dia):
    if timezone.localtime().hour >= 23:
        pytest.skip("Después de las 23:00 ya no queda una cita futura hoy")
    consulta = fabricas.servicio("Revisión", CategoriaServicio.CONSULTA, 15)
    _cita(fabricas.mascota("Rocky", "Carla"), dia["pedro"], consulta, "23:00")
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    panel = client.get("/").content.decode()
    assert 'data-aviso="proxima"' in panel and "Sin citas pendientes hoy" not in panel
