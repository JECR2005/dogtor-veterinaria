"""S1-06 · Mi cuenta > Cambiar contraseña: la nueva funciona y la anterior no (RNF-01)."""

import pytest

from seguridad import services
from seguridad.models import Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

ACTUAL = "Clave-Prueba-2026"
NUEVA = "Perro-Gato-Conejo-77"
RUTA = "/cuenta/contrasena/"


def _cambiar(client, actual=ACTUAL, nueva=NUEVA, confirmacion=None):
    datos = {"actual": actual, "nueva": nueva, "confirmacion": nueva if confirmacion is None else confirmacion}
    return client.post(RUTA, datos, follow=True)


@pytest.fixture
def sesion(client, crear_usuario):
    usuario = crear_usuario("recepcion")
    client.force_login(usuario)
    return usuario


def test_S1_06_la_nueva_funciona_y_la_anterior_no(client, sesion):
    respuesta = _cambiar(client)
    assert "Contraseña actualizada." in respuesta.content.decode()
    assert services.autenticar("recepcion", NUEVA).aceptado
    assert not services.autenticar("recepcion", ACTUAL).aceptado


def test_la_sesion_sigue_abierta_despues_del_cambio(client, sesion):
    _cambiar(client)
    assert client.get("/").status_code == 200


def test_la_pantalla_aparece_en_mi_cuenta_y_muestra_las_reglas(client, sesion):
    contenido = client.get(RUTA).content.decode()
    assert 'href="/cuenta/contrasena/"' in contenido  # enlace del menú «Mi cuenta»
    assert 'name="nueva"' in contenido
    assert "10" in contenido  # regla de longitud mínima de RNF-01


def test_contrasena_actual_incorrecta_no_cambia_nada_y_cuenta_como_intento(client, sesion):
    contenido = _cambiar(client, actual="otra-cosa").content.decode()
    assert services.MENSAJE_CONTRASENA_ACTUAL in contenido
    usuario = Usuario.objects.get(pk=sesion.pk)
    assert usuario.check_password(ACTUAL)
    assert usuario.intentos_fallidos == 1


def test_confirmacion_distinta_no_cambia_nada(client, sesion):
    contenido = _cambiar(client, confirmacion="Perro-Gato-Conejo-78").content.decode()
    assert services.MENSAJE_CONFIRMACION in contenido
    assert Usuario.objects.get(pk=sesion.pk).check_password(ACTUAL)


def test_la_nueva_debe_ser_distinta_de_la_actual(client, sesion):
    contenido = _cambiar(client, nueva=ACTUAL).content.decode()
    assert services.MENSAJE_MISMA_CONTRASENA in contenido


@pytest.mark.parametrize("debil", ["12345", "corta1", "1234567890123", "recepcion-2026"])
def test_reglas_de_rnf01_rechazan_contrasenas_debiles(client, sesion, debil):
    _cambiar(client, nueva=debil)
    assert Usuario.objects.get(pk=sesion.pk).check_password(ACTUAL)


def test_cinco_contrasenas_actuales_incorrectas_bloquean_y_cierran_la_sesion(client, sesion):
    for _ in range(4):
        _cambiar(client, actual="otra-cosa")
    respuesta = _cambiar(client, actual="otra-cosa")
    assert "Cuenta bloqueada" in respuesta.content.decode()
    assert respuesta.redirect_chain[-1][0] == "/cuenta/entrar/"
    assert Usuario.objects.get(pk=sesion.pk).esta_bloqueado
    assert client.get("/").status_code == 302


def test_sin_sesion_lleva_al_inicio_de_sesion(client):
    respuesta = client.get(RUTA)
    assert respuesta.status_code == 302
    assert respuesta.url.startswith("/cuenta/entrar/")
