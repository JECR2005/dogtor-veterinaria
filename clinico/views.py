"""Pantallas del componente «Expediente clínico» (apartado 4.2): opción Consulta clínica de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).
Consulta clínica: Veterinario ● completo; Administrador ○ consulta.

UI-11 Consulta (S3-04, S3-05): consultas del día, apertura desde la cita, captura y firma con confirmación.
UI-12 Aplicaciones (S3-07) y UI-13 Receta con PDF (S3-08, S3-09), dentro de la consulta abierta.
UI-14 Historial clínico (S3-06): línea de tiempo de la mascota.
"""

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from agenda.models import Cita
from agenda.services import citas_visibles
from catalogos.models import Mascota
from catalogos.services import mascotas_visibles
from reportes.services import pdf_desde_plantilla
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import Rol
from seguridad.permisos import requiere_permiso

from . import services
from .forms import AplicacionForm, ConsultaForm, MedicamentosFormSet, RecetaForm
from .models import Aplicacion, Consulta, ConsultaFirmada, Receta


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


def _pantalla_consulta(request, consulta, formulario=None, aplicacion_form=None):
    editable = not consulta.firmada and services.puede_atender(_empleado(request), consulta.cita)
    if editable:
        formulario = formulario or ConsultaForm(instance=consulta)
        aplicacion_form = aplicacion_form or AplicacionForm()
    contexto = {
        "consulta": consulta,
        "mascota": consulta.expediente.mascota,
        "formulario": formulario if editable else None,
        "aplicacion_form": aplicacion_form if editable else None,
        "aplicaciones": consulta.aplicaciones.select_related("lote__producto").order_by("id_aplicacion"),
        "recetas": consulta.recetas.prefetch_related("detalles__producto").order_by("id_receta"),
        "editable": editable,
        "puede_firmar": editable and services.puede_firmar(_empleado(request)),
        "faltan": services.faltantes_para_firmar(consulta),
    }
    return render(request, "clinico/consulta.html", contexto)


@requiere_permiso("consulta")
def consulta(request, id_consulta):
    """UI-11 · Consulta: editable mientras está Abierta para su veterinario; firmada, solo lectura (RD-07)."""
    consulta = _consulta_visible(request, id_consulta)
    if request.method == "POST":
        if consulta.firmada or not services.puede_atender(_empleado(request), consulta.cita):
            messages.error(
                request, services.MENSAJE_SOLO_LECTURA if consulta.firmada else "No es su consulta."
            )
            return redirect("clinico:consulta", consulta.pk)
        formulario = ConsultaForm(request.POST, instance=consulta)
        if formulario.is_valid():
            try:
                services.guardar_consulta(consulta, _empleado(request), formulario.cleaned_data)
            except (services.ErrorClinico, ConsultaFirmada) as error:
                formulario.add_error(None, str(error))
            else:
                messages.success(request, "Consulta guardada.")
                return redirect("clinico:consulta", consulta.pk)
        return _pantalla_consulta(request, consulta, formulario=formulario)
    return _pantalla_consulta(request, consulta)


# --- S3-07 · Aplicaciones (UI-12) ---------------------------------------------------
@requiere_permiso("consulta", NIVEL_COMPLETO)
@require_POST
def aplicar(request, id_consulta):
    """Registra una aplicación y descuenta el lote que caduca primero, una sola vez (RD-05, RD-09)."""
    consulta = _consulta_visible(request, id_consulta)
    formulario = AplicacionForm(request.POST)
    if formulario.is_valid():
        datos = formulario.cleaned_data
        try:
            aplicadas = services.registrar_aplicacion(
                consulta,
                _empleado(request),
                datos["producto"],
                datos["cantidad"],
                datos["dosis"],
                datos["proxima_fecha"],
            )
        except (services.ErrorClinico, ConsultaFirmada) as error:
            formulario.add_error(None, str(error))
        else:
            lotes = ", ".join(a.lote.numero_lote for a in aplicadas)
            messages.success(
                request,
                f"Aplicación registrada: {datos['producto'].nombre}, lote {lotes}. El lote ya se descontó.",
            )
            return redirect("clinico:consulta", consulta.pk)
    return _pantalla_consulta(request, consulta, aplicacion_form=formulario)


@requiere_permiso("consulta", NIVEL_COMPLETO)
@require_POST
def quitar_aplicacion(request, id_aplicacion):
    """Quita una aplicación capturada por error mientras la consulta está abierta; devuelve el lote."""
    aplicacion = get_object_or_404(
        Aplicacion.objects.select_related("lote__producto", "consulta").filter(
            consulta__cita__in=citas_visibles(request.user)
        ),
        pk=id_aplicacion,
    )
    try:
        services.quitar_aplicacion(aplicacion, _empleado(request))
    except (services.ErrorClinico, ConsultaFirmada) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Aplicación quitada; se devolvió al lote {aplicacion.lote.numero_lote}.")
    return redirect("clinico:consulta", aplicacion.consulta_id)


# --- S3-08 y S3-09 · Receta (UI-13) -------------------------------------------------------
@requiere_permiso("consulta", NIVEL_COMPLETO)
def receta(request, id_consulta):
    """Emitir una receta dentro de la consulta abierta (RD-08). No descuenta existencias (RF-07)."""
    consulta = _consulta_visible(request, id_consulta)
    if not services.puede_atender(_empleado(request), consulta.cita):
        raise Http404  # no es su consulta
    if consulta.firmada:
        messages.error(request, "La receta solo se emite dentro de una consulta abierta (RD-08).")
        return redirect("clinico:consulta", consulta.pk)
    formulario = RecetaForm(request.POST or None)
    partidas = MedicamentosFormSet(request.POST or None, prefix="medicamentos")
    if request.method == "POST" and formulario.is_valid() and partidas.is_valid():
        try:
            emitida = services.emitir_receta(
                consulta,
                _empleado(request),
                partidas.partidas(),
                formulario.cleaned_data["indicaciones_generales"],
            )
        except (services.ErrorClinico, ConsultaFirmada) as error:
            formulario.add_error(None, str(error))
        else:
            messages.success(request, f"Receta {emitida.folio} emitida. Puede descargar su PDF.")
            return redirect("clinico:consulta", consulta.pk)
    contexto = {
        "consulta": consulta,
        "mascota": consulta.expediente.mascota,
        "formulario": formulario,
        "partidas": partidas,
    }
    return render(request, "clinico/receta.html", contexto)


@requiere_permiso("consulta")
def receta_pdf(request, id_receta):
    """S3-09 · PDF de la receta en tamaño carta (RF-07, D-18)."""
    receta = get_object_or_404(
        Receta.objects.select_related(
            "consulta__empleado",
            "consulta__expediente__mascota__cliente",
            "consulta__expediente__mascota__raza__especie",
        ).filter(consulta__cita__in=citas_visibles(request.user)),
        pk=id_receta,
    )
    contexto = {
        "receta": receta,
        "consulta": receta.consulta,
        "mascota": receta.consulta.expediente.mascota,
        "veterinario": receta.consulta.empleado,
        "detalles": receta.detalles.select_related("producto").order_by("id_detalle_receta"),
    }
    respuesta = HttpResponse(
        pdf_desde_plantilla("reportes/receta.html", contexto), content_type="application/pdf"
    )
    respuesta["Content-Disposition"] = f'inline; filename="Receta-{receta.folio}.pdf"'
    return respuesta


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
