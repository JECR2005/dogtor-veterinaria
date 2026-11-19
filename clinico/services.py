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

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaProducto, Mascota, Puesto, PuestoRequerido
from inventario.models import Lote, MovimientoInventario, TipoMovimiento

from .models import (
    MENSAJE_SOLO_LECTURA,
    Aplicacion,
    Consulta,
    ConsultaFirmada,
    DetalleReceta,
    EstadoConsulta,
    Receta,
    RegistroEstetica,
    TipoAplicacion,
)

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

    Cada evento es un diccionario con fecha, tipo («consulta» o «estetica») y el registro. Las aplicaciones
    y las recetas van dentro de su consulta.
    """
    eventos = []
    consultas = (
        Consulta.objects.filter(expediente__mascota=mascota)
        .select_related("empleado", "cita__servicio")
        .prefetch_related("aplicaciones__lote__producto", "recetas")
    )
    for consulta in consultas:
        eventos.append({"fecha": consulta.fecha_hora, "tipo": "consulta", "registro": consulta})
    registros = RegistroEstetica.objects.filter(cita__mascota=mascota).select_related(
        "cita__servicio", "cita__empleado"
    )
    for registro in registros:
        eventos.append({"fecha": registro.fecha_hora, "tipo": "estetica", "registro": registro})
    return sorted(eventos, key=lambda e: e["fecha"], reverse=True)


# --- S3-07 · Aplicaciones (RF-08, RD-05, RD-09, TU-16, TI-04) ---------------------------
TIPO_POR_CATEGORIA = {
    CategoriaProducto.VACUNA: TipoAplicacion.VACUNA,
    CategoriaProducto.DESPARASITANTE: TipoAplicacion.DESPARASITANTE,
}
CATEGORIAS_APLICABLES = (
    CategoriaProducto.VACUNA,
    CategoriaProducto.DESPARASITANTE,
    CategoriaProducto.MEDICAMENTO,
)
MENSAJE_PROXIMA_FECHA = "En vacunas y desparasitantes la próxima fecha es obligatoria (RF-08)."


def _consulta_editable(consulta, empleado):
    """Bloquea la consulta y comprueba que siga Abierta y que la capture su veterinario."""
    actual = Consulta.objects.select_for_update().select_related("cita__servicio").get(pk=consulta.pk)
    if actual.firmada:
        raise ConsultaFirmada(MENSAJE_SOLO_LECTURA)
    if not puede_atender(empleado, actual.cita):
        raise ErrorClinico("Solo el veterinario asignado a la cita puede registrarlo.")
    return actual


@transaction.atomic
def registrar_aplicacion(consulta, empleado, producto, cantidad, dosis, proxima_fecha=None, hoy=None):
    """Registra la aplicación y descuenta el lote vigente que caduca primero, una sola vez (RD-09).

    Si la cantidad toma de dos lotes, queda una aplicación por lote para que cada una diga de dónde salió.
    El cobro en caja (P4) se hace con un servicio del catálogo que no descuenta existencias.
    """
    from inventario import services as inventario

    hoy = hoy or timezone.localdate()
    actual = _consulta_editable(consulta, empleado)
    if producto.categoria not in CATEGORIAS_APLICABLES or not producto.activo:
        raise ErrorClinico(f"«{producto.nombre}» no es un producto que se aplique en consulta.")
    tipo = TIPO_POR_CATEGORIA.get(producto.categoria, TipoAplicacion.OTRO)
    if tipo != TipoAplicacion.OTRO and proxima_fecha is None:
        raise ErrorClinico(MENSAJE_PROXIMA_FECHA)
    if proxima_fecha is not None and proxima_fecha <= hoy:
        raise ErrorClinico("La próxima fecha debe ser posterior a hoy.")
    dosis = " ".join((dosis or "").split())
    if not dosis:
        raise ErrorClinico("Capture la dosis (por ejemplo, «1 mL subcutánea»).")
    try:
        tomado = inventario.descontar(
            producto,
            cantidad,
            empleado,
            TipoMovimiento.APLICACION,
            referencia=f"Consulta {actual.pk}",
            hoy=hoy,
        )
    except inventario.ErrorInventario as error:
        raise ErrorClinico(str(error)) from error
    return [
        Aplicacion.objects.create(
            consulta=actual,
            lote=lote,
            tipo=tipo,
            cantidad=parte,
            dosis=dosis,
            fecha_aplicacion=hoy,
            proxima_fecha=proxima_fecha,
        )
        for lote, parte in tomado
    ]


@transaction.atomic
def quitar_aplicacion(aplicacion, empleado):
    """Corrige una aplicación capturada por error mientras la consulta sigue Abierta: devuelve al lote lo
    descontado con un movimiento de Devolución (los movimientos no se borran, RD-07) y quita la aplicación."""
    actual = Aplicacion.objects.select_related("lote__producto").get(pk=aplicacion.pk)
    _consulta_editable(actual.consulta, empleado)
    Lote.objects.filter(pk=actual.lote_id).update(
        cantidad_disponible=F("cantidad_disponible") + actual.cantidad
    )
    MovimientoInventario.objects.create(
        lote=actual.lote,
        empleado=empleado,
        tipo=TipoMovimiento.DEVOLUCION,
        cantidad=actual.cantidad,
        referencia=f"Consulta {actual.consulta_id}",
        motivo="Aplicación capturada por error",
    )
    actual.delete()


# --- S3-08 · Recetas (RF-07, RD-08, TU-15) ----------------------------------------------
def _siguiente_folio(hoy):
    prefijo = f"R-{hoy:%Y}-"
    ultimos = Receta.objects.filter(folio__startswith=prefijo).values_list("folio", flat=True)
    numero = max((int(folio.rsplit("-", 1)[1]) for folio in ultimos), default=0) + 1
    return f"{prefijo}{numero:05d}"


def emitir_receta(consulta, empleado, partidas, indicaciones_generales=None, hoy=None):
    """Emite una receta con folio dentro de una consulta Abierta (RD-08). No descuenta existencias (RF-07).

    partidas: [(producto, dosis, frecuencia, duracion_dias, indicaciones)]. Solo receta un veterinario con
    cédula (RD-01). El folio es consecutivo por año: R-2026-00001.
    """
    hoy = hoy or timezone.localdate()
    if consulta is None:
        raise ErrorClinico("Una receta solo se emite dentro de una consulta abierta (RD-08).")
    if not puede_firmar(empleado):
        raise ErrorClinico("Solo un veterinario con cédula profesional registrada puede recetar (RD-01).")
    if not partidas:
        raise ErrorClinico("Agregue al menos un medicamento a la receta.")
    productos = [p.pk for p, *_ in partidas]
    if len(productos) != len(set(productos)):
        raise ErrorClinico("Un medicamento aparece dos veces en la receta.")
    for intento in range(3):  # el folio es único: si dos recetas toman el mismo a la vez, se reintenta
        try:
            with transaction.atomic():
                actual = _consulta_editable(consulta, empleado)
                receta = Receta.objects.create(
                    consulta=actual,
                    folio=_siguiente_folio(hoy),
                    indicaciones_generales=(indicaciones_generales or "").strip() or None,
                )
                DetalleReceta.objects.bulk_create(
                    DetalleReceta(
                        receta=receta,
                        producto=producto,
                        dosis=dosis,
                        frecuencia=frecuencia,
                        duracion_dias=duracion,
                        indicaciones=(indicaciones or "").strip() or None,
                    )
                    for producto, dosis, frecuencia, duracion, indicaciones in partidas
                )
                return receta
        except IntegrityError:
            if intento == 2:
                raise
    return None  # pragma: no cover


# --- S3-12 y S3-13 · Atención de estética y aviso al veterinario (RF-10, RD-04, TI-11) -----
DIAS_DEL_AVISO = 30  # un aviso sin consulta posterior sigue a la vista del veterinario un mes


def citas_de_estetica_del_dia(dia=None, estilista=None):
    """UI-16 · Citas de estética del día (las del estilista, si se indica), con su registro si ya existe."""
    dia = dia or timezone.localdate()
    inicio = timezone.make_aware(datetime.combine(dia, time.min))
    citas = (
        Cita.objects.filter(
            fecha_hora_inicio__gte=inicio,
            fecha_hora_inicio__lt=inicio + timedelta(days=1),
            servicio__puesto_requerido=PuestoRequerido.ESTILISTA,
        )
        .exclude(estado=EstadoCita.CANCELADA)
        .select_related(
            "mascota__cliente", "mascota__raza__especie", "mascota__expediente", "empleado", "servicio"
        )
        .order_by("fecha_hora_inicio", "empleado__nombre")
    )
    if estilista is not None:
        citas = citas.filter(empleado=estilista)
    registros = {r.cita_id: r for r in RegistroEstetica.objects.filter(cita__in=citas)}
    citas = list(citas)
    for cita in citas:
        cita.registro = registros.get(cita.pk)
    return citas


def puede_registrar_estetica(empleado, cita):
    """La atención la registra el estilista asignado a la cita de estética (RD-04)."""
    return (
        empleado is not None
        and empleado.puesto == Puesto.ESTILISTA
        and cita.empleado_id == empleado.pk
        and cita.servicio.puesto_requerido == PuestoRequerido.ESTILISTA
    )


@transaction.atomic
def registrar_estetica(cita, empleado, datos, ahora=None):
    """Guarda el registro de estética y completa la cita en un solo paso (RF-10)."""
    ahora = ahora or timezone.now()
    actual = Cita.objects.select_for_update().select_related("servicio", "mascota").get(pk=cita.pk)
    if not puede_registrar_estetica(empleado, actual):
        raise ErrorClinico("Solo el estilista asignado a la cita puede registrar la atención.")
    if actual.estado != EstadoCita.PROGRAMADA:
        raise ErrorClinico(f"La cita ya está {actual.estado.lower()}; no se puede registrar otra atención.")
    if timezone.localtime(actual.fecha_hora_inicio).date() > timezone.localtime(ahora).date():
        raise ErrorClinico("La atención se registra el día de la cita, no antes.")
    if datos.get("aviso_veterinario") and not (datos.get("hallazgos") or "").strip():
        raise ErrorClinico("Para avisar al veterinario, describa el hallazgo.")
    registro = RegistroEstetica.objects.create(
        cita=actual,
        estado_pelaje_piel=datos["estado_pelaje_piel"].strip(),
        hallazgos=(datos.get("hallazgos") or "").strip() or None,
        aviso_veterinario=bool(datos.get("aviso_veterinario")),
        observaciones=(datos.get("observaciones") or "").strip() or None,
        fecha_hora=ahora,
    )
    actual.estado = EstadoCita.COMPLETADA
    actual.save(update_fields=["estado"])
    return registro


def _avisos():
    return RegistroEstetica.objects.filter(aviso_veterinario=True).select_related(
        "cita__mascota__cliente", "cita__mascota__raza__especie", "cita__empleado", "cita__servicio"
    )


def avisos_pendientes(ahora=None):
    """S3-13 · Avisos del último mes cuya mascota todavía no pasa a consulta (Inicio del veterinario)."""
    ahora = ahora or timezone.now()
    avisos = _avisos().filter(fecha_hora__gte=ahora - timedelta(days=DIAS_DEL_AVISO))
    return [
        aviso
        for aviso in avisos.order_by("-fecha_hora")
        if not Consulta.objects.filter(
            expediente__mascota_id=aviso.cita.mascota_id, fecha_hora__gte=aviso.fecha_hora
        ).exists()
    ]


def avisos_de_la_mascota(mascota, hasta=None):
    """Avisos del mes previo a la consulta, para mostrarlos al veterinario junto a las alergias."""
    hasta = hasta or timezone.now()
    return list(
        _avisos()
        .filter(
            cita__mascota=mascota,
            fecha_hora__lte=hasta,
            fecha_hora__gte=hasta - timedelta(days=DIAS_DEL_AVISO),
        )
        .order_by("-fecha_hora")
    )
