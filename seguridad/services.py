"""Servicios (reglas de negocio) del componente «Seguridad y acceso».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

- RNF-01: inicio de sesión, bloqueo al quinto intento fallido y reactivación por el Administrador (S1-04).
- RNF-01: permisos por rol en cada vista (S1-05) y cambio de contraseña (S1-06).
- RNF-03: registro en bitácora de bajas y reactivaciones (S1-07) y del resto de cambios (P2 a P5).
- RNF-08: exportación de contactos solo para el Administrador, con registro en bitácora (P5).
"""

from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import F

from .models import Rol, Usuario

# Frases que ve el usuario en UI-01 (RI-08: el mensaje dice qué pasó y qué hacer)
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_BLOQUEADA = (
    "Cuenta bloqueada por cinco intentos fallidos de contraseña. Pida al Administrador que la reactive."
)


def intentos_maximos():
    return getattr(settings, "DOGTOR_INTENTOS_MAXIMOS", 5)


class Resultado(Enum):
    ACEPTADO = "aceptado"
    CREDENCIALES_INCORRECTAS = "credenciales_incorrectas"
    BLOQUEADA = "bloqueada"


@dataclass(frozen=True)
class ResultadoAutenticacion:
    resultado: Resultado
    usuario: Usuario | None = None

    @property
    def aceptado(self):
        return self.resultado is Resultado.ACEPTADO

    @property
    def mensaje(self):
        if self.resultado is Resultado.BLOQUEADA:
            return MENSAJE_BLOQUEADA
        if self.resultado is Resultado.CREDENCIALES_INCORRECTAS:
            return MENSAJE_CREDENCIALES
        return ""


def autenticar(nombre_usuario, contrasena):
    """Usuario.autenticar del diagrama de clases (TU-13, RNF-01).

    - Usuario inexistente o dado de baja (activo = 0): «Usuario o contraseña incorrectos», sin decir cuál.
    - Cuenta bloqueada: se rechaza aunque la contraseña sea correcta, hasta que el Administrador la reactive.
    - Contraseña incorrecta: suma un intento; al llegar al quinto la cuenta queda bloqueada.
    - Contraseña correcta: el contador vuelve a cero.
    """
    nombre_usuario = (nombre_usuario or "").strip()
    try:
        usuario = Usuario.objects.select_related("empleado").get(nombre_usuario=nombre_usuario)
    except Usuario.DoesNotExist:
        # Se calcula un hash igual para que el tiempo de respuesta no revele si la cuenta existe
        make_password(contrasena)
        return ResultadoAutenticacion(Resultado.CREDENCIALES_INCORRECTAS)

    if usuario.esta_bloqueado:
        return ResultadoAutenticacion(Resultado.BLOQUEADA, usuario)

    if not usuario.check_password(contrasena or ""):
        _sumar_intento_fallido(usuario)
        if usuario.esta_bloqueado:
            return ResultadoAutenticacion(Resultado.BLOQUEADA, usuario)
        return ResultadoAutenticacion(Resultado.CREDENCIALES_INCORRECTAS, usuario)

    if not usuario.activo:
        return ResultadoAutenticacion(Resultado.CREDENCIALES_INCORRECTAS, usuario)

    if usuario.intentos_fallidos:
        Usuario.objects.filter(pk=usuario.pk).update(intentos_fallidos=0)
        usuario.intentos_fallidos = 0
    return ResultadoAutenticacion(Resultado.ACEPTADO, usuario)


def _sumar_intento_fallido(usuario):
    """Suma el intento en la base con UPDATE … + 1 para no perder intentos simultáneos."""
    with transaction.atomic():
        Usuario.objects.filter(pk=usuario.pk, intentos_fallidos__lt=intentos_maximos()).update(
            intentos_fallidos=F("intentos_fallidos") + 1
        )
        usuario.refresh_from_db(fields=["intentos_fallidos"])


class ReactivacionNoPermitida(Exception):
    pass


def cuentas_bloqueadas():
    return (
        Usuario.objects.select_related("empleado")
        .filter(intentos_fallidos__gte=intentos_maximos())
        .order_by("nombre_usuario")
    )


def reactivar_cuenta(cuenta, administrador):
    """Reactivación de una cuenta bloqueada (UI-03, RNF-01). Solo la hace un Administrador activo.

    El registro en la bitácora de auditoría se agrega con el servicio de S1-07.
    """
    if administrador.rol != Rol.ADMINISTRADOR or not administrador.is_active:
        raise ReactivacionNoPermitida("Solo el Administrador reactiva cuentas.")
    Usuario.objects.filter(pk=cuenta.pk).update(intentos_fallidos=0)
    cuenta.intentos_fallidos = 0
    return cuenta
