"""S0-16 · La plantilla base responde (con sesión desde S1-04) y la salud reporta la base (RNF-06)."""

import pytest

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_S0_inicio_muestra_la_estructura_comun(client, crear_usuario):
    client.force_login(crear_usuario("recepcion"))
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "Panel del día" in respuesta.content.decode()


def test_S0_salud_reporta_base_de_datos_disponible(client):
    respuesta = client.get("/salud/")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
