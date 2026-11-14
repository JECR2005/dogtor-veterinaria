"""Pantallas del componente «Seguridad y acceso» (apartado 4.2).

UI-01 Inicio de sesión y la reactivación de cuentas bloqueadas (S1-04). La validación del permiso del
rol en cada vista se generaliza en S1-05.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from . import services
from .menu import NIVEL_COMPLETO
from .models import Usuario


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


def _exigir_administracion(usuario):
    if not usuario.tiene_permiso("administracion", NIVEL_COMPLETO):
        raise PermissionDenied


@login_required
def cuentas_bloqueadas(request):
    """Administración > Empleados y usuarios: cuentas bloqueadas (UI-03, RNF-01)."""
    _exigir_administracion(request.user)
    return render(request, "seguridad/cuentas_bloqueadas.html", {"cuentas": services.cuentas_bloqueadas()})


@login_required
@require_POST
def reactivar(request, id_usuario):
    _exigir_administracion(request.user)
    cuenta = get_object_or_404(Usuario, pk=id_usuario)
    services.reactivar_cuenta(cuenta, request.user)
    messages.success(request, f"Cuenta «{cuenta.nombre_usuario}» reactivada.")
    return redirect("seguridad:cuentas_bloqueadas")
