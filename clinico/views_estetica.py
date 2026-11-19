"""Pantallas de Estética (apartado 4.2): opción Estética de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py.
Estética: Estilista ● completo; Veterinario y Administrador ○ consulta.

UI-16 Atención de estética (S3-12, S3-13): agenda del estilista pensada para la tableta; registro del estado
de pelaje y piel, hallazgos, aviso al veterinario y cierre de la cita (RF-10, RD-04).
"""

from datetime import date, timedelta

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from agenda.models import Cita
from catalogos.models import PuestoRequerido
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import Rol
from seguridad.permisos import requiere_permiso

from . import services
from .forms import RegistroEsteticaForm
from .models import RegistroEstetica


def _empleado(request):
    return getattr(request.user, "empleado", None)


def _dia(request):
    try:
        return date.fromisoformat(request.GET.get("fecha", ""))
    except ValueError:
        return timezone.localdate()


@requiere_permiso("estetica")
def dia(request):
    """UI-16 · Agenda de estética del día: el estilista ve la suya; Veterinario y Administrador, todas."""
    estilista = _empleado(request) if request.user.rol == Rol.ESTILISTA else None
    dia = _dia(request)
    contexto = {
        "citas": services.citas_de_estetica_del_dia(dia, estilista),
        "dia": dia,
        "hoy": timezone.localdate(),
        "anterior": dia - timedelta(days=1),
        "siguiente": dia + timedelta(days=1),
        "propias": estilista is not None,
    }
    return render(request, "estetica/dia.html", contexto)


@requiere_permiso("estetica", NIVEL_COMPLETO)
def atender(request, id_cita):
    """UI-16 · Registrar la atención: al guardar, la cita queda Completada."""
    cita = get_object_or_404(
        Cita.objects.select_related(
            "mascota__cliente", "mascota__raza__especie", "mascota__expediente", "servicio", "empleado"
        ),
        pk=id_cita,
        servicio__puesto_requerido=PuestoRequerido.ESTILISTA,
    )
    existente = RegistroEstetica.objects.filter(cita=cita).first()
    if existente:
        return redirect("estetica:registro", existente.pk)
    if not services.puede_registrar_estetica(_empleado(request), cita):
        raise Http404  # no es su cita
    formulario = RegistroEsteticaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            registro = services.registrar_estetica(cita, _empleado(request), formulario.cleaned_data)
        except services.ErrorClinico as error:
            formulario.add_error(None, str(error))
        else:
            texto = f"Atención de {cita.mascota} registrada; la cita quedó completada."
            if registro.aviso_veterinario:
                texto += " Se avisó al veterinario."
            messages.success(request, texto)
            dia = timezone.localtime(cita.fecha_hora_inicio).date()
            return redirect(f"{reverse('estetica:dia')}?fecha={dia.isoformat()}")
    contexto = {"cita": cita, "mascota": cita.mascota, "formulario": formulario}
    return render(request, "estetica/atender.html", contexto)


@requiere_permiso("estetica")
def registro(request, id_registro):
    """Registro de estética en solo lectura (lo ven el estilista, el veterinario y el Administrador)."""
    registro = get_object_or_404(
        RegistroEstetica.objects.select_related(
            "cita__mascota__cliente",
            "cita__mascota__raza__especie",
            "cita__mascota__expediente",
            "cita__servicio",
            "cita__empleado",
        ),
        pk=id_registro,
    )
    contexto = {"registro": registro, "cita": registro.cita, "mascota": registro.cita.mascota}
    return render(request, "estetica/registro.html", contexto)
