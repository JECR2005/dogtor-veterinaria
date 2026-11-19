"""Servicios (reglas de negocio) del componente «Recordatorios».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

RF-09 (S3-10, S3-11): cada día se genera la lista de clientes por contactar con su canal preferido:
- Próximas dosis de vacunas y desparasitantes que vencen en 3 días o menos (72 horas antes, TU-17).
- Citas programadas del día siguiente. El domingo no hay servicio (RNF-06): el sábado se avisa también
  a las citas del lunes.
La generación es repetible: cada aplicación o cita tiene a lo más un recordatorio. Se ejecuta al abrir la
lista y con `python manage.py generar_recordatorios` (para el Programador de tareas en P5).
"""

from datetime import datetime, time, timedelta
from urllib.parse import quote

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, PreferenciaContacto, Servicio
from clinico.models import Aplicacion, TipoAplicacion

from .models import EstadoRecordatorio, Recordatorio, TipoRecordatorio

DIAS_ANTES_DE_LA_DOSIS = 3  # RF-09: 72 horas antes
DIAS_ATRAS_EN_LA_LISTA = 7  # un pendiente que no se atendió sigue a la vista una semana


def dias_de_citas_a_avisar(hoy):
    """Mañana; si mañana es domingo (sin servicio), también el lunes."""
    manana = hoy + timedelta(days=1)
    dias = [manana]
    if manana.isoweekday() == 7:
        dias.append(manana + timedelta(days=1))
    return dias


@transaction.atomic
def generar(hoy=None):
    """Crea los recordatorios que falten para hoy. Devuelve cuántos creó."""
    hoy = hoy or timezone.localdate()
    creados = 0

    # Próximas dosis en los próximos 3 días que todavía no tienen recordatorio
    aplicaciones = (
        Aplicacion.objects.filter(
            tipo__in=[TipoAplicacion.VACUNA, TipoAplicacion.DESPARASITANTE],
            proxima_fecha__gte=hoy,
            proxima_fecha__lte=hoy + timedelta(days=DIAS_ANTES_DE_LA_DOSIS),
            recordatorios__isnull=True,
        )
        .select_related("consulta__expediente__mascota", "lote")
        .order_by("id_aplicacion")
    )
    vistas = set()
    for aplicacion in aplicaciones:
        mascota = aplicacion.consulta.expediente.mascota
        clave = (aplicacion.consulta_id, aplicacion.lote.producto_id)
        if clave in vistas or _ya_se_aplico_despues(aplicacion, mascota):
            continue  # la misma dosis repartida en dos lotes, o una dosis posterior que ya la cubre
        vistas.add(clave)
        if Recordatorio.objects.filter(
            aplicacion__consulta_id=aplicacion.consulta_id,
            aplicacion__lote__producto_id=aplicacion.lote.producto_id,
        ).exists():
            continue
        Recordatorio.objects.create(
            cliente_id=mascota.cliente_id,
            aplicacion=aplicacion,
            tipo=TipoRecordatorio.PROXIMA_DOSIS,
            fecha_objetivo=aplicacion.proxima_fecha,
        )
        creados += 1

    # Citas programadas de mañana (y del lunes, si mañana es domingo)
    for dia in dias_de_citas_a_avisar(hoy):
        inicio = timezone.make_aware(datetime.combine(dia, time.min))
        citas = Cita.objects.filter(
            estado=EstadoCita.PROGRAMADA,
            fecha_hora_inicio__gte=inicio,
            fecha_hora_inicio__lt=inicio + timedelta(days=1),
            recordatorios__isnull=True,
        ).select_related("mascota")
        for cita in citas:
            Recordatorio.objects.create(
                cliente_id=cita.mascota.cliente_id, cita=cita, tipo=TipoRecordatorio.CITA, fecha_objetivo=dia
            )
            creados += 1
    return creados


def _ya_se_aplico_despues(aplicacion, mascota):
    """¿Hay una dosis más reciente del mismo producto en otra consulta? (el mismo día cuenta la última)."""
    return (
        Aplicacion.objects.filter(
            consulta__expediente__mascota=mascota, lote__producto_id=aplicacion.lote.producto_id
        )
        .exclude(consulta_id=aplicacion.consulta_id)
        .filter(
            Q(fecha_aplicacion__gt=aplicacion.fecha_aplicacion)
            | Q(fecha_aplicacion=aplicacion.fecha_aplicacion, id_aplicacion__gt=aplicacion.pk)
        )
        .exists()
    )


def lista_del_dia(hoy=None):
    """UI-15 · Recordatorios por estado: pendientes, sin respuesta (para reintentar) y contactados hoy."""
    hoy = hoy or timezone.localdate()
    base = Recordatorio.objects.select_related(
        "cliente",
        "aplicacion__lote__producto",
        "aplicacion__consulta__expediente__mascota",
        "cita__mascota",
        "cita__servicio",
        "cita__empleado",
        "empleado",
    ).filter(fecha_objetivo__gte=hoy - timedelta(days=DIAS_ATRAS_EN_LA_LISTA))
    inicio_de_hoy = timezone.make_aware(datetime.combine(hoy, time.min))
    pendientes = list(
        base.filter(estado=EstadoRecordatorio.PENDIENTE).order_by("fecha_objetivo", "id_recordatorio")
    )
    sin_respuesta = list(
        base.filter(estado=EstadoRecordatorio.SIN_RESPUESTA).order_by("fecha_objetivo", "id_recordatorio")
    )
    contactados = list(
        base.filter(estado=EstadoRecordatorio.CONTACTADO, fecha_contacto__gte=inicio_de_hoy).order_by(
            "-fecha_contacto"
        )
    )
    for recordatorio in [*pendientes, *sin_respuesta, *contactados]:
        _describir(recordatorio, hoy)
    return {"pendientes": pendientes, "sin_respuesta": sin_respuesta, "contactados": contactados}


def pendientes(hoy=None):
    hoy = hoy or timezone.localdate()
    return Recordatorio.objects.filter(
        estado=EstadoRecordatorio.PENDIENTE, fecha_objetivo__gte=hoy - timedelta(days=DIAS_ATRAS_EN_LA_LISTA)
    )


def _describir(recordatorio, hoy):
    """Agrega lo que la recepcionista necesita a la vista: mascota, motivo, mensaje y enlaces del canal."""
    cliente = recordatorio.cliente
    if recordatorio.tipo == TipoRecordatorio.PROXIMA_DOSIS:
        aplicacion = recordatorio.aplicacion
        mascota = aplicacion.consulta.expediente.mascota
        producto = aplicacion.lote.producto.nombre
        recordatorio.mascota = mascota
        recordatorio.motivo = f"Próxima dosis: {producto}"
        mensaje = (
            f"Hola {cliente.nombre}, le saludamos de Dogtor Veterinaria. Le recordamos que {mascota.nombre} "
            f"tiene su próxima dosis de {producto} el {recordatorio.fecha_objetivo:%d/%m/%Y}. "
            "¿Le agendamos una cita?"
        )
        recordatorio.servicio_sugerido = servicio_para(aplicacion.tipo)
    else:
        cita = recordatorio.cita
        mascota = cita.mascota
        hora = timezone.localtime(cita.fecha_hora_inicio)
        recordatorio.mascota = mascota
        recordatorio.motivo = f"Cita: {cita.servicio} a las {hora:%H:%M}"
        mensaje = (
            f"Hola {cliente.nombre}, le saludamos de Dogtor Veterinaria. Le recordamos la cita de "
            f"{mascota.nombre} ({cita.servicio}) el {hora:%d/%m/%Y} a las {hora:%H:%M}. "
            "¿Nos confirma su asistencia?"
        )
        recordatorio.servicio_sugerido = None
    dias = (recordatorio.fecha_objetivo - hoy).days
    recordatorio.cuando = (
        "hoy" if dias == 0 else ("mañana" if dias == 1 else f"en {dias} días" if dias > 0 else "ya pasó")
    )
    recordatorio.mensaje = mensaje
    recordatorio.enlace = _enlace_del_canal(cliente, mensaje)


def _enlace_del_canal(cliente, mensaje):
    """Enlace para contactar por el canal preferido (RF-09): llamada, WhatsApp o correo con el texto listo."""
    if cliente.preferencia_contacto == PreferenciaContacto.WHATSAPP:
        return f"https://wa.me/52{cliente.telefono}?text={quote(mensaje)}"
    if cliente.preferencia_contacto == PreferenciaContacto.CORREO and cliente.correo:
        asunto = quote("Recordatorio de Dogtor Veterinaria")
        return f"mailto:{cliente.correo}?subject={asunto}&body={quote(mensaje)}"
    return f"tel:+52{cliente.telefono}"


def servicio_para(tipo):
    categoria = (
        CategoriaServicio.VACUNACION if tipo == TipoAplicacion.VACUNA else CategoriaServicio.DESPARASITACION
    )
    return Servicio.objects.filter(categoria=categoria, activo=True, agendable=True).order_by("pk").first()


@transaction.atomic
def registrar_resultado(recordatorio, empleado, estado, ahora=None):
    """Contactado o Sin respuesta, con quién y cuándo (CK_recordatorio_contacto_registrado)."""
    if estado not in (EstadoRecordatorio.CONTACTADO, EstadoRecordatorio.SIN_RESPUESTA):
        raise ValueError(f"Resultado no válido: {estado}")
    actual = Recordatorio.objects.select_for_update().get(pk=recordatorio.pk)
    if actual.estado == EstadoRecordatorio.CONTACTADO:
        return actual  # ya se atendió; un segundo clic no cambia nada
    actual.estado = estado
    actual.empleado = empleado
    actual.fecha_contacto = ahora or timezone.now()
    actual.save(update_fields=["estado", "empleado", "fecha_contacto"])
    return actual
