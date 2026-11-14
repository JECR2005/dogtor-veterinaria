"""Pantallas del componente «Seguridad y acceso» (apartado 4.2).

UI-01 Inicio de sesión y la reactivación de cuentas bloqueadas (S1-04). Toda vista que no sea pública
declara su permiso con `@requiere_permiso` (S1-05, seguridad/permisos.py).
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import password_validators_help_texts
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_POST

from . import services
from .menu import NIVEL_COMPLETO
from .models import Usuario
from .permisos import requiere_permiso


def _destino_seguro(request):
    destino = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=False):
        return destino
    return "inicio"


@sensitive_post_parameters("contrasena")
@csrf_protect
@never_cache
def entrar(request):
    """UI-01 · Inicio de sesión (CU-01, RNF-01)."""
    if request.user.is_authenticated:
        return redirect("inicio")

    nombre_usuario = ""
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        contrasena = request.POST.get("contrasena", "")
        if not nombre_usuario or not contrasena:
            messages.error(request, "Escriba su usuario y su contraseña.")
        else:
            usuario = authenticate(request, username=nombre_usuario, password=contrasena)
            if usuario is not None:
                login(request, usuario)
                return redirect(_destino_seguro(request))
            resultado = getattr(request, "resultado_autenticacion", None)
            messages.error(request, resultado.mensaje if resultado else services.MENSAJE_CREDENCIALES)

    contexto = {"nombre_usuario": nombre_usuario, "next": request.GET.get("next", "")}
    return render(request, "seguridad/entrar.html", contexto)


@require_POST
def salir(request):
    """Mi cuenta > Cerrar sesión. Solo por POST para que un enlace ajeno no cierre la sesión."""
    logout(request)
    messages.success(request, "Sesión cerrada.")
    return redirect("seguridad:entrar")


@requiere_permiso("administracion", NIVEL_COMPLETO)
def cuentas_bloqueadas(request):
    """Administración > Empleados y usuarios: cuentas bloqueadas (UI-03, RNF-01)."""
    return render(request, "seguridad/cuentas_bloqueadas.html", {"cuentas": services.cuentas_bloqueadas()})


@requiere_permiso("administracion", NIVEL_COMPLETO)
@require_POST
def reactivar(request, id_usuario):
    cuenta = get_object_or_404(Usuario, pk=id_usuario)
    services.reactivar_cuenta(cuenta, request.user)
    messages.success(request, f"Cuenta «{cuenta.nombre_usuario}» reactivada.")
    return redirect("seguridad:cuentas_bloqueadas")


@requiere_permiso("cuenta")
@sensitive_post_parameters("actual", "nueva", "confirmacion")
@sensitive_variables("actual", "nueva", "confirmacion")
def cambiar_contrasena(request):
    """Mi cuenta > Cambiar contraseña (S1-06, RNF-01). La sesión sigue abierta tras el cambio."""
    errores = []
    if request.method == "POST":
        actual = request.POST.get("actual", "")
        nueva = request.POST.get("nueva", "")
        confirmacion = request.POST.get("confirmacion", "")
        errores = services.cambiar_contrasena(request.user, actual, nueva, confirmacion)
        if not errores:
            update_session_auth_hash(request, request.user)
            messages.success(request, "Contraseña actualizada. Úsela la próxima vez que entre.")
            return redirect("inicio")
        if request.user.esta_bloqueado:
            logout(request)
            messages.error(request, services.MENSAJE_BLOQUEADA)
            return redirect("seguridad:entrar")
    contexto = {"errores": errores, "reglas": password_validators_help_texts()}
    return render(request, "seguridad/cambiar_contrasena.html", contexto)
