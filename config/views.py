"""Vistas transversales del sistema."""

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from seguridad.models import Rol
from seguridad.permisos import requiere_permiso
from seguridad.services import cuentas_bloqueadas


@requiere_permiso("inicio")
def inicio(request):
    """UI-02 · Panel del día por rol (S1-16): citas de hoy y avisos (Tabla 4.4, zona 4).

    - Recepción y Administrador: todas las citas de hoy, con quién las atiende.
    - Veterinario y Estilista: sus propias citas de hoy (D-17).
    Los contadores de recordatorios, inventario y estética se conectan en P2 y P3.
    """
    from agenda import services as agenda
    from agenda.models import EstadoCita

    usuario = request.user
    hoy = timezone.localdate()
    citas = agenda.citas_visibles(usuario, agenda.citas_del_dia(hoy))
    solo_las_mias = agenda.puesto_visible(usuario) is not None
    if solo_las_mias:
        citas = citas.filter(empleado=usuario.empleado)
    citas = list(citas)
    ahora = timezone.now()
    for cita in citas:  # marca las que ya terminaron y siguen sin completarse
        cita.por_cerrar = cita.estado == EstadoCita.PROGRAMADA and cita.fecha_hora_fin <= ahora
    contexto = {
        "hoy": hoy,
        "citas": citas,
        "solo_las_mias": solo_las_mias,
        "total": sum(c.estado != EstadoCita.CANCELADA for c in citas),
        "programadas": sum(c.estado == EstadoCita.PROGRAMADA for c in citas),
        "completadas": sum(c.estado == EstadoCita.COMPLETADA for c in citas),
        "proxima": next(
            (c for c in citas if c.estado == EstadoCita.PROGRAMADA and c.fecha_hora_inicio >= ahora), None
        ),
    }
    if usuario.rol == Rol.ADMINISTRADOR:
        contexto["cuentas_bloqueadas"] = cuentas_bloqueadas().count()
    return render(request, "inicio.html", contexto)


@requiere_permiso("inicio")
def ayuda(request):
    """LV-03 punto 10 · Ayuda: la guía de usuario del apartado 4.6.2 para el rol de quien entra (DEF-004).

    Muestra lo que ya existe en el prototipo actual; cada prototipo agrega sus procedimientos.
    """
    return render(request, "ayuda.html", {"rol": request.user.rol})


def salud(request):
    """Verificación de disponibilidad para el monitoreo externo (RNF-06, R15)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        estado, codigo = "ok", 200
    except Exception:  # noqa: BLE001 - cualquier falla de la base debe reportarse como caída
        estado, codigo = "sin_base_de_datos", 503
    return JsonResponse({"estado": estado}, status=codigo)
