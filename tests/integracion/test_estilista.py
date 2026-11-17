"""DEF-002 · Tabla 4.9: el Estilista consulta «solo la mascota de su cita» en Clientes y mascotas."""

import pytest

from agenda import services as agenda
from catalogos.models import CategoriaServicio, Puesto
from seguridad.models import Rol, Usuario
from tests import fabricas
from tests.fabricas import en

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def escenario():
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    firulais = fabricas.mascota("Firulais", "Ana")  # tiene baño con Mario
    michi = fabricas.mascota("Michi", "Bruno")  # solo consulta con Laura
    agenda.agendar(firulais, mario, bano, en("10:00"))
    agenda.agendar(michi, laura, consulta, en("10:00"))
    cuenta = Usuario.objects.create_user("mario", "Clave-Prueba-2026", empleado=mario, rol=Rol.ESTILISTA)
    return {"cuenta": cuenta, "firulais": firulais, "michi": michi}


def test_DEF002_el_estilista_solo_ve_a_los_clientes_y_mascotas_de_sus_citas(client, escenario):
    client.force_login(escenario["cuenta"])
    lista = client.get("/clientes/").content.decode()
    assert "Ana" in lista and "Bruno" not in lista
    assert "Bruno" not in client.get("/clientes/", {"q": "michi"}).content.decode()  # ni buscando
    assert client.get(f"/clientes/mascotas/{escenario['firulais'].pk}/").status_code == 200
    assert client.get(f"/clientes/mascotas/{escenario['michi'].pk}/").status_code == 404
    assert client.get(f"/clientes/{escenario['firulais'].cliente_id}/").status_code == 200
    assert client.get(f"/clientes/{escenario['michi'].cliente_id}/").status_code == 404


def test_DEF002_el_veterinario_sigue_viendo_a_todos(client, crear_usuario, escenario):
    client.force_login(crear_usuario("vet", rol=Rol.VETERINARIO))
    lista = client.get("/clientes/").content.decode()
    assert "Ana" in lista and "Bruno" in lista
    assert client.get(f"/clientes/mascotas/{escenario['michi'].pk}/").status_code == 200
