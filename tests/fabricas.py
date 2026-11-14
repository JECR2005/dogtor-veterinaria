"""Datos de prueba reutilizables para la agenda (S1-12 a S1-14). Todo es ficticio."""

from datetime import date, datetime, time, timedelta

from django.utils import timezone

from catalogos.models import (
    Cliente,
    Empleado,
    Especie,
    HorarioLaboral,
    Mascota,
    PreferenciaContacto,
    Puesto,
    Raza,
    Servicio,
    Sexo,
)


def lunes_proximo():
    hoy = timezone.localdate()
    return hoy + timedelta(days=7 - hoy.weekday() + 7)  # un lunes dentro de 8 a 14 días


LUNES = lunes_proximo()


def en(hora, dia=None):
    """Fecha y hora local de la clínica, por ejemplo en("10:15")."""
    return timezone.make_aware(datetime.combine(dia or LUNES, time.fromisoformat(hora)))


def empleado(puesto, cedula=None, jornada=("09:00", "19:00"), nombre=None):
    persona = Empleado.objects.create(
        nombre=nombre or puesto,
        apellidos="Prueba",
        puesto=puesto,
        cedula_profesional=cedula if puesto == Puesto.VETERINARIO else None,
        fecha_ingreso=date(2026, 1, 5),
    )
    for dia in range(1, 7):
        HorarioLaboral.objects.create(
            empleado=persona,
            dia_semana=dia,
            hora_entrada=time.fromisoformat(jornada[0]),
            hora_salida=time.fromisoformat(jornada[1]),
        )
    return persona


def servicio(nombre, categoria, minutos):
    return Servicio.objects.create(
        nombre=nombre,
        categoria=categoria,
        precio="400.00",
        duracion_min=minutos,
        puesto_requerido=Servicio.puesto_para(categoria),
    )


def mascota(nombre="Firulais", cliente_nombre="Ana"):
    cliente = Cliente.objects.create(
        nombre=cliente_nombre,
        apellido_paterno="López",
        telefono="8331234567",
        preferencia_contacto=PreferenciaContacto.TELEFONO,
        acepto_aviso_privacidad=True,
    )
    especie, _ = Especie.objects.get_or_create(nombre="Perro")
    raza, _ = Raza.objects.get_or_create(especie=especie, nombre="Mestizo")
    return Mascota.objects.create(cliente=cliente, raza=raza, nombre=nombre, sexo=Sexo.MACHO)
