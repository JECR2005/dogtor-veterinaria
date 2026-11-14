"""S1-05 · Ninguna pantalla queda abierta: todas las rutas declaran su permiso (RNF-01, RI-11).

Recorre las rutas del sistema. Si alguien agrega una vista sin `@requiere_permiso` y sin incluirla en
VISTAS_PUBLICAS, esta prueba falla en el pull request. Además prueba cada ruta sin parámetros con
cada rol escribiendo la dirección (adelanto de TS-01, actividad S1-20).
"""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver

from seguridad.menu import NIVEL_CONSULTA, ROLES
from seguridad.permisos import VISTAS_PUBLICAS

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def _rutas(patrones=None, prefijo="", espacio=""):
    """(nombre completo, ruta, vista, tiene parámetros) de cada ruta registrada."""
    for patron in get_resolver().url_patterns if patrones is None else patrones:
        if isinstance(patron, URLResolver):
            nuevo_espacio = f"{espacio}{patron.namespace}:" if patron.namespace else espacio
            yield from _rutas(patron.url_patterns, prefijo + str(patron.pattern), nuevo_espacio)
        elif isinstance(patron, URLPattern):
            ruta = prefijo + str(patron.pattern)
            yield f"{espacio}{patron.name}", "/" + ruta, patron.callback, "<" in ruta


RUTAS = list(_rutas())
RUTAS_PROTEGIDAS = [
    (nombre, ruta, vista.dogtor_permiso)
    for nombre, ruta, vista, con_parametros in RUTAS
    if nombre not in VISTAS_PUBLICAS and not con_parametros
]


def test_toda_ruta_es_publica_a_proposito_o_declara_su_permiso():
    sin_permiso = [
        nombre
        for nombre, _ruta, vista, _p in RUTAS
        if nombre not in VISTAS_PUBLICAS and not hasattr(vista, "dogtor_permiso")
    ]
    assert sin_permiso == [], f"Vistas sin @requiere_permiso: {sin_permiso}"


def test_las_vistas_publicas_existen():
    assert VISTAS_PUBLICAS <= {nombre for nombre, *_ in RUTAS}


@pytest.mark.parametrize("nombre, ruta, permiso", RUTAS_PROTEGIDAS, ids=[r[0] for r in RUTAS_PROTEGIDAS])
def test_sin_sesion_ninguna_ruta_protegida_abre(client, nombre, ruta, permiso):
    respuesta = client.get(ruta)
    assert respuesta.status_code == 302
    assert respuesta.url.startswith("/cuenta/entrar/")


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("nombre, ruta, permiso", RUTAS_PROTEGIDAS, ids=[r[0] for r in RUTAS_PROTEGIDAS])
def test_cada_rol_entra_solo_a_lo_que_le_da_la_tabla_4_9(client, crear_usuario, rol, nombre, ruta, permiso):
    usuario = crear_usuario("usuario", rol=rol)
    client.force_login(usuario)
    opcion, nivel = permiso
    respuesta = client.get(ruta)
    if usuario.tiene_permiso(opcion, nivel or NIVEL_CONSULTA):
        assert respuesta.status_code == 200
    else:
        assert respuesta.status_code == 403
        assert "Acceso denegado" in respuesta.content.decode()
