"""D-17 · Cada rol ve solo la agenda que le toca.

Veterinario: sus citas y las de otros veterinarios. Estilista: sus citas y las de otros estilistas.
Recepción y Administrador: todas. Aplica al calendario, la lista del día, el detalle y la ficha de la mascota.
"""

from datetime import timedelta

import pytest

from agenda import services
from catalogos.models import CategoriaServicio, Puesto
from seguridad.models import Rol
from tests import fabricas
from tests.fabricas import LUNES, en

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

RANGO = {
    "start": f"{LUNES.isoformat()}T00:00:00-06:00",
    "end": f"{(LUNES + timedelta(days=7)).isoformat()}T00:00:00-06:00",
}


@pytest.fixture
def agenda():
    """Laura y Pedro (veterinarios) y Sofía (estilista), cada uno con una cita el lunes."""
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    pedro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    sofia = fabricas.empleado(Puesto.ESTILISTA, nombre="Sofía")
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    firulais = fabricas.mascota("Firulais", "Ana")
    return {
        "laura": services.agendar(firulais, laura, consulta, en("10:00")),
        "pedro": services.agendar(fabricas.mascota("Michi", "Bruno"), pedro, consulta, en("10:00")),
        "sofia": services.agendar(firulais, sofia, bano, en("12:00")),
        "firulais": firulais,
        "empleados": {"laura": laura, "pedro": pedro, "sofia": sofia},
    }


def _entrar(client, crear_usuario, rol):
    client.force_login(crear_usuario("usuario", rol=rol))
    return client


def _titulos(client, **extra):
    return sorted(e["title"] for e in client.get("/agenda/eventos/", {**RANGO, **extra}).json())


TODAS = ["Firulais · Baño", "Firulais · Consulta general", "Michi · Consulta general"]


def test_D17_el_veterinario_ve_las_citas_de_veterinarios_y_no_las_de_estetica(client, crear_usuario, agenda):
    _entrar(client, crear_usuario, Rol.VETERINARIO)
    assert _titulos(client) == ["Firulais · Consulta general", "Michi · Consulta general"]

    lista = client.get("/agenda/dia/", {"fecha": LUNES.isoformat()}).content.decode()
    assert "Consulta general" in lista and "Baño" not in lista

    calendario = client.get("/agenda/").content.decode()
    assert "Laura Prueba (Veterinario)" in calendario and "Sofía Prueba" not in calendario

    assert client.get(f"/agenda/citas/{agenda['pedro'].pk}/").status_code == 200
    assert client.get(f"/agenda/citas/{agenda['sofia'].pk}/").status_code == 404

    ficha = client.get(f"/clientes/mascotas/{agenda['firulais'].pk}/").content.decode()
    assert "Consulta general" in ficha and "Baño" not in ficha


def test_D17_el_estilista_solo_ve_la_agenda_de_estetica(client, crear_usuario, agenda):
    _entrar(client, crear_usuario, Rol.ESTILISTA)
    assert _titulos(client) == ["Firulais · Baño"]
    assert client.get(f"/agenda/citas/{agenda['laura'].pk}/").status_code == 404
    assert client.get(f"/agenda/citas/{agenda['sofia'].pk}/").status_code == 200


def test_D17_filtrar_por_un_empleado_de_otro_puesto_no_muestra_sus_citas(client, crear_usuario, agenda):
    _entrar(client, crear_usuario, Rol.VETERINARIO)
    assert "Firulais · Baño" not in _titulos(client, empleado=agenda["empleados"]["sofia"].pk)
    lista = client.get(
        "/agenda/dia/", {"fecha": LUNES.isoformat(), "empleado": agenda["empleados"]["sofia"].pk}
    ).content.decode()
    assert "Baño" not in lista


@pytest.mark.parametrize("rol", [Rol.RECEPCIONISTA, Rol.ADMINISTRADOR])
def test_D17_recepcion_y_administrador_ven_todas(client, crear_usuario, agenda, rol):
    _entrar(client, crear_usuario, rol)
    assert _titulos(client) == TODAS
    calendario = client.get("/agenda/").content.decode()
    assert "Laura Prueba" in calendario and "Sofía Prueba" in calendario
    assert client.get(f"/agenda/citas/{agenda['sofia'].pk}/").status_code == 200


def test_D17_regla_por_rol():
    class Usuario:
        def __init__(self, rol):
            self.rol = rol

    assert services.puesto_visible(Usuario(Rol.VETERINARIO)) == Puesto.VETERINARIO
    assert services.puesto_visible(Usuario(Rol.ESTILISTA)) == Puesto.ESTILISTA
    assert services.puesto_visible(Usuario(Rol.RECEPCIONISTA)) is None
    assert services.puesto_visible(Usuario(Rol.ADMINISTRADOR)) is None
