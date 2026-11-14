"""Vistas transversales del sistema."""

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from seguridad.models import Rol
from seguridad.services import cuentas_bloqueadas


@login_required
def inicio(request):
    """Panel del día (UI-02). Requiere sesión (RNF-01); los contadores se completan en S1-16 y en P2 a P3."""
    contexto = {}
    if request.user.rol == Rol.ADMINISTRADOR:
        contexto["cuentas_bloqueadas"] = cuentas_bloqueadas().count()
    return render(request, "inicio.html", contexto)


def salud(request):
    """Verificación de disponibilidad para el monitoreo externo (RNF-06, R15)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        estado, codigo = "ok", 200
    except Exception:  # noqa: BLE001 - cualquier falla de la base debe reportarse como caída
        estado, codigo = "sin_base_de_datos", 503
    return JsonResponse({"estado": estado}, status=codigo)
