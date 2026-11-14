"""S1-05 · Decorador requiere_permiso: Tabla 4.9 aplicada en el servidor (RNF-01, RI-11)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from seguridad.menu import NIVEL_COMPLETO, NIVEL_CONSULTA
from seguridad.models import Rol
from seguridad.permisos import nivel_requerido, requiere_permiso

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

fabrica = RequestFactory()


@requiere_permiso("agenda")
def vista_agenda(request):
    return HttpResponse(request.dogtor_nivel)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def vista_inventario(request):
    return HttpResponse("ok")


def _solicitud(usuario, metodo="get", ruta="/agenda/"):
    solicitud = getattr(fabrica, metodo)(ruta)
    solicitud.user = usuario
    return solicitud


def test_sin_sesion_lleva_al_inicio_de_sesion_con_el_destino():
    respuesta = vista_agenda(_solicitud(AnonymousUser(), ruta="/agenda/semana/"))
    assert respuesta.status_code == 302
    assert respuesta.url == "/cuenta/entrar/?next=/agenda/semana/"


def test_rol_sin_la_opcion_recibe_acceso_denegado(crear_usuario):
    estilista = crear_usuario("estilista", rol=Rol.ESTILISTA)
    with pytest.raises(PermissionDenied):
        vista_inventario(_solicitud(estilista))


def test_nivel_consulta_puede_ver_pero_no_modificar(crear_usuario):
    veterinario = crear_usuario("veterinario", rol=Rol.VETERINARIO)  # ○ en Agenda
    respuesta = vista_agenda(_solicitud(veterinario))
    assert respuesta.status_code == 200
    assert respuesta.content.decode() == NIVEL_CONSULTA
    with pytest.raises(PermissionDenied):
        vista_agenda(_solicitud(veterinario, "post"))


def test_nivel_completo_puede_modificar(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)  # ● en Agenda
    respuesta = vista_agenda(_solicitud(recepcion, "post"))
    assert respuesta.content.decode() == NIVEL_COMPLETO


def test_nivel_completo_exigido_tambien_para_ver(crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    assert vista_inventario(_solicitud(admin)).status_code == 200


def test_cuenta_bloqueada_no_pasa_aunque_su_rol_tenga_la_opcion(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    recepcion.intentos_fallidos = 5
    with pytest.raises(PermissionDenied):
        vista_agenda(_solicitud(recepcion))


def test_opcion_inexistente_falla_al_declarar_la_vista():
    with pytest.raises(KeyError):
        requiere_permiso("opcion-que-no-existe")


def test_nivel_inexistente_falla_al_declarar_la_vista():
    with pytest.raises(ValueError):
        requiere_permiso("agenda", "total")


@pytest.mark.parametrize(
    "metodo, esperado",
    [("GET", NIVEL_CONSULTA), ("HEAD", NIVEL_CONSULTA), ("POST", NIVEL_COMPLETO), ("DELETE", NIVEL_COMPLETO)],
)
def test_el_metodo_decide_el_nivel_si_la_vista_no_lo_fija(metodo, esperado):
    assert nivel_requerido(metodo) == esperado
    assert nivel_requerido(metodo, NIVEL_COMPLETO) == NIVEL_COMPLETO
