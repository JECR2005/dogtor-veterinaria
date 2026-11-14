"""Pantallas del componente «Agenda y citas» (apartado 4.2).

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).

UI-07 Agenda y cita: calendario por empleado con FullCalendar (S1-14, D-07), lista del día, nueva cita,
detalle, reprogramar, cancelar con motivo y completar (S1-13).
Agenda: Recepcionista ● completo; Administrador, Veterinario y Estilista ○ consulta.
"""

from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogos.models import Empleado, EstatusMascota, Mascota, Servicio
from catalogos.services import buscar_clientes
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import CancelarForm, CitaForm, ReprogramarForm, servicios_por_categoria
from .models import Cita, EstadoCita


def _fecha(texto, por_omision):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return por_omision


def _cuando(cita):
    return timezone.localtime(cita.fecha_hora_inicio).strftime("%d/%m/%Y a las %H:%M")


def _empleados_con_horario():
    return Empleado.objects.filter(activo=True, horarios__isnull=False).distinct().order_by("nombre")


def _empleado_elegido(request, empleados):
    if request.GET.get("empleado", "").isdigit():
        return empleados.filter(pk=request.GET["empleado"]).first()
    return None


@requiere_permiso("agenda")
def calendario(request):
    """UI-07 · Calendario de día y semana con filtro por empleado (RF-05, D-07)."""
    empleados = _empleados_con_horario()
    contexto = {
        "empleados": empleados,
        "empleado": _empleado_elegido(request, empleados),
        "fecha": _fecha(request.GET.get("fecha"), timezone.localdate()),
    }
    return render(request, "agenda/calendario.html", contexto)


def _fecha_hora(texto):
    """Fechas que manda FullCalendar («2026-11-16T00:00:00-06:00» o «2026-11-16»)."""
    try:
        valor = datetime.fromisoformat((texto or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return timezone.make_aware(valor) if timezone.is_naive(valor) else valor


@requiere_permiso("agenda")
def eventos(request):
    """Citas del rango visible del calendario, como eventos de FullCalendar (JSON)."""
    inicio, fin = _fecha_hora(request.GET.get("start")), _fecha_hora(request.GET.get("end"))
    if inicio is None or fin is None or fin <= inicio:
        return JsonResponse({"error": "Rango de fechas no válido."}, status=400)
    empleado = _empleado_elegido(request, _empleados_con_horario())
    citas = services.citas_entre(
        inicio, fin, empleado, incluir_canceladas=request.GET.get("canceladas") == "1"
    )
    return JsonResponse([services.evento_de(cita) for cita in citas], safe=False)


@requiere_permiso("agenda")
def dia(request):
    """UI-07 · Citas de un día, con filtro por empleado."""
    hoy = timezone.localdate()
    fecha = _fecha(request.GET.get("fecha"), hoy)
    empleados = _empleados_con_horario()
    empleado = _empleado_elegido(request, empleados)
    contexto = {
        "fecha": fecha,
        "hoy": hoy,
        "anterior": fecha - timedelta(days=1),
        "siguiente": fecha + timedelta(days=1),
        "empleados": empleados,
        "empleado": empleado,
        "citas": services.citas_del_dia(fecha, empleado),
    }
    return render(request, "agenda/dia.html", contexto)


def _elegir_mascota(request):
    """Primer paso de «Nueva cita» cuando no viene de la ficha: buscar al cliente y su mascota."""
    texto = request.GET.get("q", "").strip()
    clientes = buscar_clientes(texto).prefetch_related("mascotas__raza") if texto else []
    # Si viene del calendario, se conserva el día y la hora elegidos
    seleccion = {clave: request.GET[clave] for clave in ("fecha", "hora") if request.GET.get(clave)}
    contexto = {"texto": texto, "clientes": clientes, "seleccion": urlencode(seleccion)}
    return render(request, "agenda/elegir_mascota.html", contexto)


@requiere_permiso("agenda", NIVEL_COMPLETO)
def nueva(request):
    """UI-07 · Nueva cita para una mascota (RF-05, RD-02, RD-04)."""
    if not request.GET.get("mascota", "").isdigit():
        return _elegir_mascota(request)
    mascota = get_object_or_404(
        Mascota.objects.select_related("cliente", "raza__especie"),
        pk=request.GET["mascota"],
        cliente__activo=True,
        estatus=EstatusMascota.ACTIVA,
    )
    id_servicio = request.POST.get("servicio") or request.GET.get("servicio")
    servicio = None
    if id_servicio and str(id_servicio).isdigit():
        servicio = Servicio.objects.filter(pk=id_servicio, activo=True, agendable=True).first()

    inicial = {
        "servicio": servicio,
        "fecha": request.GET.get("fecha") or timezone.localdate(),
        "hora": request.GET.get("hora"),
    }
    formulario = CitaForm(request.POST or None, initial=inicial, servicio=servicio)
    if request.method == "POST" and formulario.is_valid():
        datos = formulario.cleaned_data
        try:
            cita = services.agendar(
                mascota, datos["empleado"], datos["servicio"], formulario.inicio(), datos["motivo"]
            )
        except services.CitaRechazada as error:
            formulario.add_error(None, str(error))
        else:
            messages.success(
                request,
                f"Cita agendada: {mascota} con {cita.empleado.nombre_completo}, el {_cuando(cita)}.",
            )
            return redirect("agenda:cita", id_cita=cita.pk)
    contexto = {
        "formulario": formulario,
        "mascota": mascota,
        "servicio": servicio,
        "servicios_agrupados": servicios_por_categoria()[1:],
    }
    return render(request, "agenda/nueva.html", contexto)


@requiere_permiso("agenda")
def cita(request, id_cita):
    """UI-07 · Detalle de la cita con sus acciones."""
    cita = get_object_or_404(
        Cita.objects.select_related("mascota__cliente", "mascota__raza__especie", "empleado", "servicio"),
        pk=id_cita,
    )
    contexto = {
        "cita": cita,
        "programada": cita.estado == EstadoCita.PROGRAMADA,
        "ya_empezo": cita.fecha_hora_inicio <= timezone.now(),
        "form_cancelar": CancelarForm(),
    }
    return render(request, "agenda/cita.html", contexto)


@requiere_permiso("agenda", NIVEL_COMPLETO)
def reprogramar(request, id_cita):
    """Reprogramar: el espacio anterior se libera de inmediato (RF-05)."""
    cita = get_object_or_404(
        Cita.objects.select_related("mascota__cliente", "empleado", "servicio"),
        pk=id_cita,
        estado=EstadoCita.PROGRAMADA,
    )
    local = timezone.localtime(cita.fecha_hora_inicio)
    inicial = {"empleado": cita.empleado, "fecha": local.date(), "hora": local.time()}
    formulario = ReprogramarForm(request.POST or None, initial=inicial, servicio=cita.servicio)
    if request.method == "POST" and formulario.is_valid():
        try:
            cita = services.reprogramar(cita, formulario.inicio(), formulario.cleaned_data["empleado"])
        except services.CitaRechazada as error:
            formulario.add_error(None, str(error))
        else:
            messages.success(
                request, f"Cita reprogramada para el {_cuando(cita)} con {cita.empleado.nombre_completo}."
            )
            return redirect("agenda:cita", id_cita=cita.pk)
    return render(request, "agenda/reprogramar.html", {"formulario": formulario, "cita": cita})


@requiere_permiso("agenda", NIVEL_COMPLETO)
@require_POST
def cancelar(request, id_cita):
    """Cancelar con motivo obligatorio (RF-05). El espacio queda libre de inmediato."""
    cita = get_object_or_404(Cita, pk=id_cita)
    try:
        services.cancelar(cita, request.POST.get("motivo"))
    except services.CitaRechazada as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Cita cancelada. El espacio quedó libre en la agenda.")
    return redirect("agenda:cita", id_cita=cita.pk)


@requiere_permiso("agenda", NIVEL_COMPLETO)
@require_POST
def completar(request, id_cita):
    cita = get_object_or_404(Cita, pk=id_cita)
    try:
        services.completar(cita)
    except services.CitaRechazada as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Cita marcada como Completada.")
    return redirect("agenda:cita", id_cita=cita.pk)
