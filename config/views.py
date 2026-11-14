"""Vistas transversales del sistema."""

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from seguridad.models import Rol
from seguridad.permisos import requiere_permiso
from seguridad.services import cuentas_bloqueadas


@requiere_permiso("inicio")
def inicio(request):
    """Panel del día (UI-02), con la opción «inicio» de la Tabla 4.9 (RNF-01).

    Los contadores se completan en S1-16 y en P2 a P3.
    """
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
