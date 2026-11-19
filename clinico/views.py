"""Pantallas del componente «Expediente clínico» (apartado 4.2): opción Consulta clínica de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).
Consulta clínica: Veterinario ● completo; Administrador ○ consulta.

UI-11 Consulta (S3-04, S3-05): consultas del día, apertura desde la cita, captura y firma con confirmación.
UI-14 Historial clínico (S3-06): línea de tiempo de la mascota.
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from agenda.models import Cita
from agenda.services import citas_visibles
from catalogos.models import Mascota
from catalogos.services import mascotas_visibles
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import Rol
from seguridad.permisos import requiere_permiso

from . import services
from .forms import ConsultaForm
from .models import Consulta, ConsultaFirmada


def _empleado(request):
    return getattr(request.user, "empleado", None)


def _consulta_visible(request, id_consulta):
    """D-17: el veterinario ve las consultas de las citas de veterinarios; el Administrador, todas."""
    return get_object_or_404(
        Consulta.objects.select_related(
            "expediente__mascota__cliente", "expediente__mascota__raza__especie", "cita__servicio", "empleado"
        ).filter(cita__in=citas_visibles(request.user)),
        pk=id_consulta,
    )


@requiere_permiso("consulta")
def dia(request):
    """UI-11 · Consultas del día: el veterinario ve las suyas; el Administrador, las de todos."""
    veterinario = _empleado(request) if request.user.rol == Rol.VETERINARIO else None
    citas = list(services.citas_clinicas_del_dia(veterinario=veterinario))
    contexto = {"citas": citas, "hoy": timezone.localdate(), "propias": veterinario is not None}
    return render(request, "clinico/dia.html", contexto)


@requiere_permiso("consulta", NIVEL_COMPLETO)
def atender(request, id_cita):
    """Abre la consulta de una cita: muestra la alerta de alergias y pide síntomas y peso."""
    cita = get_object_or_404(
        Cita.objects.select_related(
            "mascota__cliente", "mascota__raza__especie", "mascota__expediente", "servicio"
        ),
        pk=id_cita,
    )
    existente = Consulta.objects.filter(cita=cita).first()
    if existente:
        return redirect("clinico:consulta", existente.pk)
    if not services.puede_atender(_empleado(request), cita):
        raise Http404  # no es su cita
    formulario = ConsultaForm(request.POST or None, initial={"peso_kg": cita.mascota.peso_actual})
    if request.method == "POST" and formulario.is_valid():
        try:
            consulta = services.abrir_consulta(cita, _empleado(request), formulario.cleaned_data)
        except services.ErrorClinico as error:
            formulario.add_error(None, str(error))
        else:
            messages.success(
                request, f"Consulta de {cita.mascota} abierta. Puede seguir capturando y firmar al terminar."
            )
            return redirect("clinico:consulta", consulta.pk)
    contexto = {"cita": cita, "mascota": cita.mascota, "formulario": formulario}
    return render(request, "clinico/atender.html", contexto)


@requiere_permiso("consulta")
def consulta(request, id_consulta):
    """UI-11 · Consulta: editable mientras está Abierta para su veterinario; firmada, solo lectura (RD-07)."""
    consulta = _consulta_visible(request, id_consulta)
    editable = not consulta.firmada and services.puede_atender(_empleado(request), consulta.cita)
    formulario = None
    if editable:
        formulario = ConsultaForm(request.POST or None, instance=consulta)
        if request.method == "POST" and formulario.is_valid():
            try:
                services.guardar_consulta(consulta, _empleado(request), formulario.cleaned_data)
            except (services.ErrorClinico, ConsultaFirmada) as error:
                formulario.add_error(None, str(error))
            else:
                messages.success(request, "Consulta guardada.")
                return redirect("clinico:consulta", consulta.pk)
    elif request.method == "POST":
        messages.error(
            request, str(services.MENSAJE_SOLO_LECTURA if consulta.firmada else "No es su consulta.")
        )
        return redirect("clinico:consulta", consulta.pk)
    contexto = {
        "consulta": consulta,
        "mascota": consulta.expediente.mascota,
        "formulario": formulario,
        "editable": editable,
        "puede_firmar": editable and services.puede_firmar(_empleado(request)),
        "faltan": services.faltantes_para_firmar(consulta),
    }
    return render(request, "clinico/consulta.html", contexto)


@requiere_permiso("consulta", NIVEL_COMPLETO)
def firmar(request, id_consulta):
    """Firmar con confirmación (RI-04): después la consulta queda en solo lectura (RD-07)."""
    consulta = _consulta_visible(request, id_consulta)
    if request.method == "POST":
        try:
            services.firmar(consulta, _empleado(request))
        except (services.ErrorClinico, ConsultaFirmada) as error:
            messages.error(request, str(error))
        else:
            messages.success(
                request,
                f"Consulta firmada. La cita quedó completada y el peso de {consulta.expediente.mascota} "
                f"se actualizó a {consulta.peso_kg} kg.",
            )
        return redirect("clinico:consulta", consulta.pk)
    if consulta.firmada:
        return redirect("clinico:consulta", consulta.pk)
    contexto = {
        "consulta": consulta,
        "mascota": consulta.expediente.mascota,
        "faltan": services.faltantes_para_firmar(consulta),
        "puede_firmar": services.puede_firmar(_empleado(request)),
        "sin_cedula": services.MENSAJE_SIN_CEDULA,
    }
    return render(request, "clinico/firmar.html", contexto)


@requiere_permiso("consulta")
def historial(request, id_mascota):
    """UI-14 · Historial clínico de la mascota."""
    mascota = get_object_or_404(
        mascotas_visibles(
            request.user, Mascota.objects.select_related("cliente", "raza__especie", "expediente")
        ),
        pk=id_mascota,
    )
    contexto = {"mascota": mascota, "eventos": services.historial(mascota)}
    return render(request, "clinico/historial.html", contexto)
