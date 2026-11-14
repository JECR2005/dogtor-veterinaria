"""Servicios (reglas de negocio) del componente «Agenda y citas».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

S1-12 · Validación y creación de una cita (procedimiento del apartado 4.3, RF-05):
  1. Obtener la duración del servicio y calcular la hora de fin.
  2. Verificar que el puesto del empleado sea compatible con el servicio (RD-04).
  3. Verificar que la cita caiga dentro del horario laboral del empleado ese día (RD-02).
  4. Buscar citas activas del mismo empleado que se traslapen (RD-02). Hay empalme si la nueva
     empieza antes de que termine otra y termina después de que esa empiece; si una termina justo
     cuando la otra inicia, no hay empalme.
  4b. D-16: la mascota tampoco puede tener otra cita activa que se traslape, con ningún empleado.
  5. Si todo es válido, crear la cita como Programada. Si no, mostrar «Fuera de horario laboral» o
     «Empalme de horario» y no guardar nada.

Los pasos 4 y 5 corren en una transacción que bloquea al empleado (SELECT … WITH (UPDLOCK)): dos
recepcionistas que agendan al mismo empleado a la vez se forman una detrás de otra, y la segunda ve
la cita de la primera. Así no se cuelan dos citas en el mismo espacio.
"""

from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from catalogos.models import Empleado, EstatusMascota, Mascota, Puesto
from seguridad.models import Rol

from .models import Cita, EstadoCita

# Frases del documento (Tabla 4.29, TU-01, TU-03): las ve la recepcionista tal cual
MENSAJE_FUERA_DE_HORARIO = "Fuera de horario laboral"
MENSAJE_EMPALME = "Empalme de horario"
# D-16: una mascota no puede estar en dos citas a la vez, aunque sean con empleados distintos
MENSAJE_EMPALME_MASCOTA = "La mascota ya tiene una cita a esa hora"


class CitaRechazada(Exception):
    """La cita no cumple una regla; el mensaje se muestra tal cual (RI-08) y no se guarda nada."""


def calcular_fin(servicio, inicio):
    """Paso 1 (RF-04): la duración del servicio define la hora de fin."""
    return servicio.calcular_fin(inicio)


def horario_cubre(empleado, inicio, fin):
    """Paso 3 (RD-02, TU-03): alguna jornada del empleado contiene la cita completa."""
    return any(horario.cubre(inicio, fin) for horario in empleado.horarios.all())


def citas_que_se_empalman(empleado, inicio, fin, excluir=None):
    """Paso 4 (RD-02): citas no canceladas del empleado que se traslapan con [inicio, fin)."""
    citas = Cita.objects.filter(
        empleado=empleado, fecha_hora_inicio__lt=fin, fecha_hora_fin__gt=inicio
    ).exclude(estado=EstadoCita.CANCELADA)
    if excluir is not None:
        citas = citas.exclude(pk=excluir.pk)
    return citas


def hay_empalme(empleado, inicio, fin, excluir=None):
    """Agenda.hayEmpalme del diagrama de clases (TU-01, TU-02)."""
    return citas_que_se_empalman(empleado, inicio, fin, excluir).exists()


def citas_de_la_mascota_que_se_empalman(mascota, inicio, fin, excluir=None):
    """D-16: citas no canceladas de la misma mascota que se traslapan, con cualquier empleado."""
    citas = Cita.objects.filter(
        mascota=mascota, fecha_hora_inicio__lt=fin, fecha_hora_fin__gt=inicio
    ).exclude(estado=EstadoCita.CANCELADA)
    if excluir is not None:
        citas = citas.exclude(pk=excluir.pk)
    return citas


def validar_cita(mascota, empleado, servicio, inicio, excluir=None, ahora=None):
    """Aplica los pasos 1 a 4 y devuelve la hora de fin. Lanza CitaRechazada si algo no se cumple.

    `excluir` es la cita que se reprograma (no choca consigo misma).
    """
    if timezone.is_naive(inicio):
        inicio = timezone.make_aware(inicio)
    ahora = ahora or timezone.now()
    if inicio < ahora:
        raise CitaRechazada("No se pueden agendar citas en una fecha u hora que ya pasó.")
    if not mascota.cliente.activo:
        raise CitaRechazada("El cliente está dado de baja; no se le pueden agendar citas.")
    if mascota.estatus != EstatusMascota.ACTIVA:
        raise CitaRechazada(f"La mascota está {mascota.estatus.lower()}; no se le pueden agendar citas.")
    if not servicio.activo or not servicio.agendable:
        raise CitaRechazada(f"El servicio «{servicio}» no se agenda.")

    fin = calcular_fin(servicio, inicio)  # paso 1
    if not empleado.puede_prestar(servicio):  # paso 2 (RD-04)
        raise CitaRechazada(
            f"El servicio «{servicio}» lo presta un {servicio.puesto_requerido}; "
            f"{empleado.nombre_completo} es {empleado.puesto}. Elija otro empleado."
        )
    if not horario_cubre(empleado, inicio, fin):  # paso 3 (RD-02)
        raise CitaRechazada(MENSAJE_FUERA_DE_HORARIO)
    if hay_empalme(empleado, inicio, fin, excluir):  # paso 4 (RD-02)
        raise CitaRechazada(MENSAJE_EMPALME)
    otra = (
        citas_de_la_mascota_que_se_empalman(mascota, inicio, fin, excluir)
        .select_related("empleado", "servicio")
        .first()
    )
    if otra is not None:  # D-16
        hora = timezone.localtime(otra.fecha_hora_inicio)
        raise CitaRechazada(
            f"{MENSAJE_EMPALME_MASCOTA}: {otra.servicio} a las {hora:%H:%M} "
            f"con {otra.empleado.nombre_completo}"
        )
    return fin


def empleados_para(servicio):
    """RD-04 · TI-02: la lista de empleados del formulario muestra solo el puesto compatible."""
    return (
        Empleado.objects.filter(activo=True, puesto=servicio.puesto_requerido)
        .prefetch_related("horarios")
        .order_by("nombre", "apellidos")
    )


def agendar(mascota, empleado, servicio, inicio, motivo=None):
    """Paso 5 (RF-05): crea la cita Programada si pasa todas las reglas; si no, no guarda nada."""
    if timezone.is_naive(inicio):
        inicio = timezone.make_aware(inicio)
    with transaction.atomic():
        # Bloquea al empleado y a la mascota: las citas simultáneas para cualquiera de los dos se
        # validan una después de otra (RD-02 y D-16)
        empleado = Empleado.objects.select_for_update().get(pk=empleado.pk)
        mascota = Mascota.objects.select_for_update().select_related("cliente").get(pk=mascota.pk)
        fin = validar_cita(mascota, empleado, servicio, inicio)
        return Cita.objects.create(
            mascota=mascota,
            empleado=empleado,
            servicio=servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=fin,
            estado=EstadoCita.PROGRAMADA,
            motivo=(motivo or "").strip() or None,
        )


# --- S1-13 · Reprogramar, cancelar y completar (RF-05) ---------------------------
MENSAJE_SOLO_PROGRAMADAS = "Solo se modifican citas Programadas; esta cita está {estado}."


def _bloquear_cita(cita):
    actual = Cita.objects.select_for_update().select_related("mascota__cliente", "servicio").get(pk=cita.pk)
    if actual.estado != EstadoCita.PROGRAMADA:
        raise CitaRechazada(MENSAJE_SOLO_PROGRAMADAS.format(estado=actual.estado.lower()))
    return actual


def reprogramar(cita, nuevo_inicio, empleado=None):
    """Cambia la fecha, la hora o el empleado de una cita Programada (RF-05).

    El espacio anterior se libera de inmediato porque es la misma cita la que se mueve; la nueva
    hora pasa por las mismas reglas que una cita nueva (RD-02, RD-04).
    """
    if timezone.is_naive(nuevo_inicio):
        nuevo_inicio = timezone.make_aware(nuevo_inicio)
    with transaction.atomic():
        actual = _bloquear_cita(cita)
        destino = Empleado.objects.select_for_update().get(pk=(empleado or actual.empleado).pk)
        Mascota.objects.select_for_update().get(pk=actual.mascota_id)  # D-16
        fin = validar_cita(actual.mascota, destino, actual.servicio, nuevo_inicio, excluir=actual)
        actual.empleado = destino
        actual.fecha_hora_inicio = nuevo_inicio
        actual.fecha_hora_fin = fin
        actual.save(update_fields=["empleado", "fecha_hora_inicio", "fecha_hora_fin"])
    return actual


def cancelar(cita, motivo):
    """Cancela una cita Programada con su motivo (RF-05). El espacio queda libre de inmediato."""
    motivo = " ".join((motivo or "").split())
    if not motivo:
        raise CitaRechazada("Escriba el motivo de la cancelación.")
    if len(motivo) > 150:
        raise CitaRechazada("El motivo de la cancelación admite hasta 150 caracteres.")
    with transaction.atomic():
        actual = _bloquear_cita(cita)
        actual.estado = EstadoCita.CANCELADA
        actual.motivo_cancelacion = motivo
        actual.save(update_fields=["estado", "motivo_cancelacion"])
    return actual


def completar(cita, ahora=None):
    """Marca como Completada una cita Programada que ya empezó (RF-05).

    En P3 la consulta firmada la completa sola (TI-08); aquí la completa la recepcionista.
    """
    ahora = ahora or timezone.now()
    with transaction.atomic():
        actual = _bloquear_cita(cita)
        if actual.fecha_hora_inicio > ahora:
            raise CitaRechazada("Una cita que todavía no empieza no se puede completar.")
        actual.estado = EstadoCita.COMPLETADA
        actual.save(update_fields=["estado"])
    return actual


def citas_del_dia(dia, empleado=None):
    """Citas de un día (hora local), con todo lo que muestra la agenda."""
    inicio = timezone.make_aware(datetime.combine(dia, time.min))
    fin = inicio + timedelta(days=1)
    citas = (
        Cita.objects.filter(fecha_hora_inicio__gte=inicio, fecha_hora_inicio__lt=fin)
        .select_related("mascota__cliente", "mascota__raza__especie", "empleado", "servicio")
        .order_by("fecha_hora_inicio", "empleado__nombre")
    )
    if empleado is not None:
        citas = citas.filter(empleado=empleado)
    return citas


# --- S1-14 · Calendario por empleado (UI-07, D-07) --------------------------------
COLOR_ESTADO = {
    EstadoCita.PROGRAMADA: "#0d6efd",
    EstadoCita.COMPLETADA: "#198754",
    EstadoCita.CANCELADA: "#6c757d",
}
MAXIMO_DIAS_CALENDARIO = 62


def citas_entre(inicio, fin, empleado=None, incluir_canceladas=False):
    """Citas que caen (aunque sea en parte) entre dos fechas, para el calendario."""
    if (fin - inicio).days > MAXIMO_DIAS_CALENDARIO:
        fin = inicio + timedelta(days=MAXIMO_DIAS_CALENDARIO)
    citas = (
        Cita.objects.filter(fecha_hora_inicio__lt=fin, fecha_hora_fin__gt=inicio)
        .select_related("mascota__cliente", "empleado", "servicio")
        .order_by("fecha_hora_inicio")
    )
    if empleado is not None:
        citas = citas.filter(empleado=empleado)
    if not incluir_canceladas:
        citas = citas.exclude(estado=EstadoCita.CANCELADA)
    return citas


def evento_de(cita):
    """Una cita en el formato de eventos de FullCalendar. El estado va en el texto, no solo en el color."""
    return {
        "id": cita.pk,
        "title": f"{cita.mascota} · {cita.servicio}",
        "start": timezone.localtime(cita.fecha_hora_inicio).isoformat(),
        "end": timezone.localtime(cita.fecha_hora_fin).isoformat(),
        "url": f"/agenda/citas/{cita.pk}/",
        "backgroundColor": COLOR_ESTADO[cita.estado],
        "borderColor": COLOR_ESTADO[cita.estado],
        "extendedProps": {
            "estado": cita.estado,
            "empleado": cita.empleado.nombre_completo,
            "cliente": str(cita.mascota.cliente),
            "telefono": cita.mascota.cliente.telefono,
        },
    }


# --- D-17 · Qué agenda ve cada rol -------------------------------------------------
# Recepción y Administrador ven la agenda de todos. Veterinario y Estilista ven solo las citas de su
# mismo puesto (las suyas y las de sus compañeros), no las del otro puesto.
PUESTO_VISIBLE_POR_ROL = {
    Rol.VETERINARIO: Puesto.VETERINARIO,
    Rol.ESTILISTA: Puesto.ESTILISTA,
}


def puesto_visible(usuario):
    """Puesto cuyas citas puede ver el usuario, o None si puede ver todas."""
    return PUESTO_VISIBLE_POR_ROL.get(usuario.rol)


def citas_visibles(usuario, citas=None):
    """Filtra un conjunto de citas a las que el rol del usuario puede ver (D-17)."""
    citas = Cita.objects.all() if citas is None else citas
    puesto = puesto_visible(usuario)
    return citas if puesto is None else citas.filter(empleado__puesto=puesto)


def empleados_visibles(usuario, empleados):
    puesto = puesto_visible(usuario)
    return empleados if puesto is None else empleados.filter(puesto=puesto)
