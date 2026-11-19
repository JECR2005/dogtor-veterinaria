"""Pantallas del componente «Recordatorios» (apartado 4.2): opción Recordatorios de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).
Recordatorios: Recepcionista ● completo; Administrador ○ consulta.

UI-15 Recordatorios del día (S3-10, S3-11): lista con el canal preferido, Contactado, Sin respuesta y agendar.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .models import EstadoRecordatorio, Recordatorio, TipoRecordatorio


@requiere_permiso("recordatorios")
def lista(request):
    """UI-15 · Genera los recordatorios que falten y muestra la lista del día."""
    services.generar()
    contexto = {**services.lista_del_dia(), "hoy": timezone.localdate()}
    return render(request, "recordatorios/lista.html", contexto)


@requiere_permiso("recordatorios", NIVEL_COMPLETO)
@require_POST
def resultado(request, id_recordatorio):
    """Registra Contactado o Sin respuesta. «Contactado y agendar» abre la nueva cita con la mascota lista."""
    recordatorio = get_object_or_404(
        Recordatorio.objects.select_related(
            "cliente", "aplicacion__consulta__expediente__mascota", "cita__mascota"
        ),
        pk=id_recordatorio,
    )
    accion = request.POST.get("accion")
    estado = EstadoRecordatorio.SIN_RESPUESTA if accion == "sin_respuesta" else EstadoRecordatorio.CONTACTADO
    services.registrar_resultado(recordatorio, request.user.empleado, estado)
    if accion == "agendar" and recordatorio.tipo == TipoRecordatorio.PROXIMA_DOSIS:
        aplicacion = recordatorio.aplicacion
        parametros = {
            "mascota": aplicacion.consulta.expediente.mascota_id,
            "fecha": aplicacion.proxima_fecha.isoformat(),
        }
        servicio = services.servicio_para(aplicacion.tipo)
        if servicio:
            parametros["servicio"] = servicio.pk
        messages.success(request, f"{recordatorio.cliente} contactado. Agende la siguiente dosis.")
        return redirect(f"{reverse('agenda:nueva')}?{urlencode(parametros)}")
    texto = (
        "contactado"
        if estado == EstadoRecordatorio.CONTACTADO
        else "sin respuesta; puede volver a intentarlo"
    )
    messages.success(request, f"{recordatorio.cliente}: {texto}.")
    return redirect("recordatorios:lista")
