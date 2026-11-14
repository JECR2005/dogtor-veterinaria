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
  5. Si todo es válido, crear la cita como Programada. Si no, mostrar «Fuera de horario laboral» o
     «Empalme de horario» y no guardar nada.

Los pasos 4 y 5 corren en una transacción que bloquea al empleado (SELECT … WITH (UPDLOCK)): dos
recepcionistas que agendan al mismo empleado a la vez se forman una detrás de otra, y la segunda ve
la cita de la primera. Así no se cuelan dos citas en el mismo espacio.
"""

from django.db import transaction
from django.utils import timezone

from catalogos.models import Empleado, EstatusMascota

from .models import Cita, EstadoCita

# Frases del documento (Tabla 4.29, TU-01, TU-03): las ve la recepcionista tal cual
MENSAJE_FUERA_DE_HORARIO = "Fuera de horario laboral"
MENSAJE_EMPALME = "Empalme de horario"


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
        # Bloquea al empleado: las citas simultáneas para él se validan una después de otra
        empleado = Empleado.objects.select_for_update().get(pk=empleado.pk)
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
