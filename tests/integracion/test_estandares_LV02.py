"""LV-02 puntos 2 y 3 · Nombre de la aplicación y etiquetas como las define el documento (S1-22)."""

import pytest

from catalogos.forms import ClienteForm
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.mark.parametrize("ruta", ["/cuenta/entrar/", "/", "/clientes/", "/agenda/"])
def test_LV02_punto2_el_nombre_de_la_aplicacion_es_el_mismo_en_cada_vista(client, crear_usuario, ruta):
    if ruta != "/cuenta/entrar/":
        client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    pagina = client.get(ruta).content.decode()
    assert "Dogtor: Veterinaria &amp; Petcare</title>" in pagina


def test_LV02_punto3_la_etiqueta_es_la_del_diccionario_de_datos():
    assert ClienteForm().fields["preferencia_contacto"].label == "Preferencia de contacto"
