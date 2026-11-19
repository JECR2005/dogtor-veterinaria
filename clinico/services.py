"""Servicios (reglas de negocio) del componente «Expediente clínico».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

- RF-06, RD-01 y RD-07: consulta ligada a una cita, firma con cédula y solo lectura después (S3-04, S3-05).
- RF-06: historial de la mascota (S3-06).
- RF-07 y RD-08: receta con folio dentro de una consulta abierta, sin descontar existencias (S3-08).
- RF-08 y RD-09: aplicación que descuenta una sola vez el lote que caduca primero (S3-07).
- RF-10: registro de estética y aviso al veterinario (S3-12, S3-13).
"""

from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import Mascota, Puesto, PuestoRequerido

from .models import MENSAJE_SOLO_LECTURA, Consulta, ConsultaFirmada, EstadoConsulta

MENSAJE_SIN_CEDULA = "Solo un veterinario con cédula profesional registrada puede firmar (RD-01)."


class ErrorClinico(Exception):
    """Operación clínica rechazada; el mensaje dice qué ocurrió y qué hacer (RI-08)."""


# --- S3-04 · Consultas del día y apertura -----------------------------------------
def citas_clinicas_del_dia(dia=None, veterinario=None):
    """Citas del día que atiende un veterinario (UI-11), con su consulta si ya se abrió."""
    dia = dia or timezone.localdate()
    inicio = timezone.make_aware(datetime.combine(dia, time.min))
    citas = (
        Cita.objects.filter(
            fecha_hora_inicio__gte=inicio,
            fecha_hora_inicio__lt=inicio + timedelta(days=1),
            servicio__puesto_requerido=PuestoRequerido.VETERINARIO,
        )
        .exclude(estado=EstadoCita.CANCELADA)
        .select_related(
            "mascota__cliente", "mascota__raza__especie", "mascota__expediente", "empleado", "servicio"
        )
        .order_by("fecha_hora_inicio", "empleado__nombre")
    )
    if veterinario is not None:
        citas = citas.filter(empleado=veterinario)
    consultas = {c.cita_id: c for c in Consulta.objects.filter(cita__in=citas)}
    for cita in citas:
        cita.consulta_abierta = consultas.get(cita.pk)
    return citas


def puede_atender(empleado, cita):
    """La consulta la abre y la captura el veterinario asignado a la cita."""
    return (
        empleado is not None
        and empleado.puesto == Puesto.VETERINARIO
        and cita.empleado_id == empleado.pk
        and cita.servicio.puesto_requerido == PuestoRequerido.VETERINARIO
    )


@transaction.atomic
def abrir_consulta(cita, empleado, datos):
    """Crea la consulta de una cita Programada con los datos mínimos (síntomas y peso, Tabla 3.42)."""
    cita = Cita.objects.select_for_update().select_related("mascota", "servicio").get(pk=cita.pk)
    if Consulta.objects.filter(cita=cita).exists():
        raise ErrorClinico("Esta cita ya tiene su consulta; ábrala desde la lista del día.")
    if cita.estado != EstadoCita.PROGRAMADA:
        raise ErrorClinico(f"La cita está {cita.estado.lower()}; solo se atiende una cita programada.")
    if not puede_atender(empleado, cita):
        raise ErrorClinico("Solo el veterinario asignado a la cita puede atenderla.")
    return Consulta.objects.create(
        expediente=cita.mascota.expediente, cita=cita, empleado=empleado, **_campos(datos)
    )


CAMPOS_CONSULTA = ("sintomas", "peso_kg", "temperatura_c", "diagnostico", "tratamiento", "observaciones")


def _campos(datos):
    return {campo: datos.get(campo) for campo in CAMPOS_CONSULTA}


# --- S3-05 · Captura y firma (RD-01, RD-07, TI-08) ----------------------------------
@transaction.atomic
def guardar_consulta(consulta, empleado, datos):
    """Guarda los cambios de una consulta Abierta. Una firmada es de solo lectura (RD-07, TU-14)."""
    actual = Consulta.objects.select_for_update().select_related("cita__servicio").get(pk=consulta.pk)
    if actual.firmada:
        raise ConsultaFirmada(MENSAJE_SOLO_LECTURA)
    if not puede_atender(empleado, actual.cita):
        raise ErrorClinico("Solo el veterinario asignado a la cita puede capturar la consulta.")
    for campo, valor in _campos(datos).items():
        setattr(actual, campo, valor)
    actual.save()
    return actual


def puede_firmar(empleado):
    """RD-01: puesto Veterinario y cédula profesional registrada."""
    return (
        empleado is not None
        and empleado.puesto == Puesto.VETERINARIO
        and bool((empleado.cedula_profesional or "").strip())
    )


def faltantes_para_firmar(consulta):
    """Lo que falta capturar antes de firmar: síntomas, peso y diagnóstico."""
    faltan = []
    if not (consulta.sintomas or "").strip():
        faltan.append("síntomas")
    if not consulta.peso_kg:
        faltan.append("peso")
    if not (consulta.diagnostico or "").strip():
        faltan.append("diagnóstico")
    return faltan


@transaction.atomic
def firmar(consulta, empleado, ahora=None):
    """Firma la consulta (RF-06): queda en solo lectura, completa la cita y actualiza el peso (TI-08)."""
    ahora = ahora or timezone.now()
    actual = (
        Consulta.objects.select_for_update()
        .select_related("cita__servicio", "expediente")
        .get(pk=consulta.pk)
    )
    if actual.firmada:
        raise ConsultaFirmada(MENSAJE_SOLO_LECTURA)
    if not puede_firmar(empleado):
        raise ErrorClinico(MENSAJE_SIN_CEDULA)
    if not puede_atender(empleado, actual.cita):
        raise ErrorClinico("Solo el veterinario asignado a la cita puede firmar la consulta.")
    faltan = faltantes_para_firmar(actual)
    if faltan:
        raise ErrorClinico(f"Antes de firmar capture: {', '.join(faltan)}.")
    actual.estado = EstadoConsulta.FIRMADA
    actual.fecha_firma = ahora
    actual.empleado = empleado
    actual.save()
    Cita.objects.filter(pk=actual.cita_id).update(estado=EstadoCita.COMPLETADA)
    Mascota.objects.filter(pk=actual.expediente.mascota_id).update(peso_actual=actual.peso_kg)
    return actual


# --- S3-06 · Historial clínico (UI-14) -------------------------------------------------
def historial(mascota):
    """Línea de tiempo de la mascota, de lo más reciente a lo más antiguo (RF-06).

    Cada evento es un diccionario con fecha, tipo y el registro. En P3 se agregan las aplicaciones, las
    recetas y la estética conforme se construyen (bloques C y E).
    """
    eventos = []
    consultas = (
        Consulta.objects.filter(expediente__mascota=mascota)
        .select_related("empleado", "cita__servicio")
        .prefetch_related("aplicaciones__lote__producto", "recetas")
    )
    for consulta in consultas:
        eventos.append({"fecha": consulta.fecha_hora, "tipo": "consulta", "registro": consulta})
    return sorted(eventos, key=lambda e: e["fecha"], reverse=True)
