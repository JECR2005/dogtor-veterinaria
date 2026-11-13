"""Vistas transversales del sistema."""

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render


def inicio(request):
    """Panel del día (UI-02). En Sprint 0 solo muestra la estructura común de la pantalla (Tabla 4.4)."""
    return render(request, "inicio.html")


def salud(request):
    """Verificación de disponibilidad para el monitoreo externo (RNF-06, R15)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        estado, codigo = "ok", 200
    except Exception:  # noqa: BLE001 - cualquier falla de la base debe reportarse como caída
        estado, codigo = "sin_base_de_datos", 503
    return JsonResponse({"estado": estado}, status=codigo)
