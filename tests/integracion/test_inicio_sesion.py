"""S1-04 · UI-01 Inicio y cierre de sesión, bloqueo y reactivación por el Administrador (RNF-01)."""

import pytest
from django.urls import reverse

from seguridad import services
from seguridad.models import Rol, Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CLAVE = "Clave-Prueba-2026"
ENTRAR = "/cuenta/entrar/"


def _entrar(client, nombre, contrasena, **extra):
    return client.post(ENTRAR, {"nombre_usuario": nombre, "contrasena": contrasena, **extra}, follow=True)


def test_sin_sesion_el_inicio_lleva_a_la_pantalla_de_entrada(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(ENTRAR)


def test_la_pantalla_de_entrada_muestra_usuario_y_contrasena(client):
    contenido = client.get(ENTRAR).content.decode()
    assert 'name="nombre_usuario"' in contenido
    assert 'name="contrasena"' in contenido
    assert 'type="password"' in contenido


def test_entrada_correcta_abre_el_panel_del_rol(client, crear_usuario):
    crear_usuario("recepcion")
    respuesta = _entrar(client, "recepcion", CLAVE)
    contenido = respuesta.content.decode()
    assert respuesta.redirect_chain[-1][0] in ("/", reverse("inicio"))
    assert "Panel del día" in contenido
    assert "Recepcionista" in contenido
    assert Usuario.objects.get(nombre_usuario="recepcion").last_login is not None


def test_entrada_respeta_el_destino_interno_y_rechaza_uno_externo(client, crear_usuario):
    crear_usuario("recepcion")
    respuesta = client.post(
        ENTRAR, {"nombre_usuario": "recepcion", "contrasena": CLAVE, "next": "https://ejemplo.com/"}
    )
    assert respuesta.url == reverse("inicio")


def test_contrasena_incorrecta_muestra_el_mensaje_sin_revelar_cual_dato_fallo(client, crear_usuario):
    crear_usuario("recepcion")
    contenido = _entrar(client, "recepcion", "incorrecta").content.decode()
    assert services.MENSAJE_CREDENCIALES in contenido
    assert 'value="recepcion"' in contenido  # conserva el usuario escrito
    assert "_auth_user_id" not in client.session


def test_campos_vacios_piden_usuario_y_contrasena(client):
    contenido = _entrar(client, "", "").content.decode()
    assert "Escriba su usuario y su contraseña." in contenido


def test_TU13_quinto_intento_muestra_el_aviso_de_cuenta_bloqueada(client, crear_usuario):
    crear_usuario("recepcion")
    for _ in range(4):
        assert services.MENSAJE_CREDENCIALES in _entrar(client, "recepcion", "incorrecta").content.decode()
    contenido = _entrar(client, "recepcion", "incorrecta").content.decode()
    assert "Cuenta bloqueada" in contenido
    # Ya bloqueada, tampoco entra con la contraseña correcta
    contenido = _entrar(client, "recepcion", CLAVE).content.decode()
    assert "Cuenta bloqueada" in contenido
    assert "_auth_user_id" not in client.session


def test_cerrar_sesion_solo_por_post(client, crear_usuario):
    crear_usuario("recepcion")
    client.force_login(Usuario.objects.get(nombre_usuario="recepcion"))
    assert client.get("/cuenta/salir/").status_code == 405
    respuesta = client.post("/cuenta/salir/", follow=True)
    assert "Sesión cerrada." in respuesta.content.decode()
    assert client.get("/").status_code == 302


def test_una_sesion_abierta_se_pierde_si_la_cuenta_se_bloquea(client, crear_usuario):
    usuario = crear_usuario("recepcion")
    client.force_login(usuario)
    Usuario.objects.filter(pk=usuario.pk).update(intentos_fallidos=5)
    assert client.get("/").status_code == 302


def test_el_administrador_ve_y_reactiva_las_cuentas_bloqueadas(client, crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cuenta = crear_usuario("estilista", rol=Rol.ESTILISTA)
    Usuario.objects.filter(pk=cuenta.pk).update(intentos_fallidos=5)
    client.force_login(admin)

    panel = client.get("/").content.decode()
    assert 'data-aviso="cuentas_bloqueadas">1<' in panel

    lista = client.get("/cuenta/bloqueadas/").content.decode()
    assert "estilista" in lista

    respuesta = client.post(f"/cuenta/bloqueadas/{cuenta.pk}/reactivar/", follow=True)
    assert "Cuenta «estilista» reactivada." in respuesta.content.decode()
    assert Usuario.objects.get(pk=cuenta.pk).intentos_fallidos == 0
    assert "No hay cuentas bloqueadas." in respuesta.content.decode()


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA])
def test_otros_roles_no_reactivan_cuentas_aunque_escriban_la_direccion(client, crear_usuario, rol):
    usuario = crear_usuario("usuario", rol=rol)
    cuenta = crear_usuario("bloqueada")
    Usuario.objects.filter(pk=cuenta.pk).update(intentos_fallidos=5)
    client.force_login(usuario)
    lista = client.get("/cuenta/bloqueadas/")
    assert lista.status_code == 403
    assert "Acceso denegado" in lista.content.decode()
    assert client.post(f"/cuenta/bloqueadas/{cuenta.pk}/reactivar/").status_code == 403
    assert Usuario.objects.get(pk=cuenta.pk).esta_bloqueado
