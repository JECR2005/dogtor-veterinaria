"""TU-13 · Usuario.autenticar: bloqueo al quinto intento fallido (RNF-01, Tabla 4.12).

Es una prueba de unidad del servicio (sin interfaz); necesita la base porque el contador de intentos
vive en la tabla usuario.
"""

import pytest

from seguridad import services
from seguridad.models import Rol, Usuario
from seguridad.services import Resultado

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

CLAVE = "Clave-Prueba-2026"


def _fallar(nombre, veces):
    for _ in range(veces):
        resultado = services.autenticar(nombre, "incorrecta")
    return resultado


def test_TU13_con_cuatro_intentos_fallidos_la_cuenta_sigue_activa(crear_usuario):
    crear_usuario("recepcion")
    resultado = _fallar("recepcion", 4)
    assert resultado.resultado is Resultado.CREDENCIALES_INCORRECTAS
    assert resultado.mensaje == services.MENSAJE_CREDENCIALES
    usuario = Usuario.objects.get(nombre_usuario="recepcion")
    assert usuario.intentos_fallidos == 4
    assert not usuario.esta_bloqueado
    assert services.autenticar("recepcion", CLAVE).aceptado


def test_TU13_con_el_quinto_intento_fallido_la_cuenta_se_bloquea(crear_usuario):
    crear_usuario("recepcion")
    resultado = _fallar("recepcion", 5)
    assert resultado.resultado is Resultado.BLOQUEADA
    assert "bloqueada" in resultado.mensaje
    assert Usuario.objects.get(nombre_usuario="recepcion").esta_bloqueado


def test_TU13_cuenta_bloqueada_no_entra_ni_con_la_contrasena_correcta(crear_usuario):
    crear_usuario("recepcion")
    _fallar("recepcion", 5)
    resultado = services.autenticar("recepcion", CLAVE)
    assert resultado.resultado is Resultado.BLOQUEADA
    assert not resultado.aceptado


def test_TU13_el_contador_no_pasa_del_maximo(crear_usuario):
    crear_usuario("recepcion")
    _fallar("recepcion", 8)
    assert Usuario.objects.get(nombre_usuario="recepcion").intentos_fallidos == 5


def test_entrada_correcta_reinicia_el_contador(crear_usuario):
    crear_usuario("recepcion")
    _fallar("recepcion", 3)
    assert services.autenticar("recepcion", CLAVE).aceptado
    assert Usuario.objects.get(nombre_usuario="recepcion").intentos_fallidos == 0


def test_usuario_inexistente_recibe_el_mismo_mensaje_que_una_contrasena_incorrecta():
    resultado = services.autenticar("nadie", "lo-que-sea")
    assert resultado.resultado is Resultado.CREDENCIALES_INCORRECTAS
    assert resultado.mensaje == services.MENSAJE_CREDENCIALES
    assert resultado.usuario is None


def test_cuenta_dada_de_baja_no_entra(crear_usuario):
    crear_usuario("recepcion", activo=False)
    resultado = services.autenticar("recepcion", CLAVE)
    assert not resultado.aceptado
    assert resultado.mensaje == services.MENSAJE_CREDENCIALES


def test_el_administrador_reactiva_una_cuenta_bloqueada(crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cuenta = crear_usuario("recepcion")
    _fallar("recepcion", 5)
    assert list(services.cuentas_bloqueadas()) == [Usuario.objects.get(pk=cuenta.pk)]
    services.reactivar_cuenta(cuenta, admin)
    assert Usuario.objects.get(pk=cuenta.pk).intentos_fallidos == 0
    assert services.autenticar("recepcion", CLAVE).aceptado


def test_solo_el_administrador_reactiva_cuentas(crear_usuario):
    recepcion = crear_usuario("recepcion")
    cuenta = crear_usuario("estilista", rol=Rol.ESTILISTA)
    _fallar("estilista", 5)
    with pytest.raises(services.ReactivacionNoPermitida):
        services.reactivar_cuenta(cuenta, recepcion)
    assert Usuario.objects.get(pk=cuenta.pk).esta_bloqueado
