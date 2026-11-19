"""Datos de prueba reutilizables (agenda desde S1-12; inventario desde S2-04). Todo es ficticio."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.utils import timezone

from catalogos.models import (
    CategoriaProducto,
    Cliente,
    Empleado,
    Especie,
    HorarioLaboral,
    Mascota,
    PreferenciaContacto,
    Producto,
    Proveedor,
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


# --- Inventario y compras (P2) --------------------------------------------------
def proveedor(razon_social="Distribuidora de Prueba", **campos):
    return Proveedor.objects.create(
        razon_social=razon_social, telefono=campos.pop("telefono", "8330000001"), **campos
    )


def producto(codigo="PRB-001", nombre="Vacuna de prueba", stock_minimo=10, **campos):
    valores = {
        "categoria": CategoriaProducto.VACUNA,
        "unidad_medida": "Dosis",
        "precio_venta": Decimal("150.00"),
    }
    valores.update(campos)
    return Producto.objects.create(codigo=codigo, nombre=nombre, stock_minimo=stock_minimo, **valores)


def lote(producto, cantidad, dias_para_caducar=180, numero=None):
    """Lote con su existencia; `dias_para_caducar=None` si el producto no caduca (negativo: ya venció)."""
    from inventario.models import Lote

    hoy = timezone.localdate()
    return Lote.objects.create(
        producto=producto,
        numero_lote=numero or f"{producto.codigo}-{Lote.objects.filter(producto=producto).count() + 1}",
        fecha_caducidad=None if dias_para_caducar is None else hoy + timedelta(days=dias_para_caducar),
        cantidad_disponible=Decimal(str(cantidad)),
    )


def pedido(proveedor, empleado, partidas):
    """Pedido Pendiente. partidas: [(producto, cantidad, costo)]."""
    from inventario.services import guardar_pedido

    return guardar_pedido(proveedor, empleado, [(p, c, Decimal(str(costo))) for p, c, costo in partidas])


# --- Expediente clínico (P3) ------------------------------------------------------
def cita_de_hoy(mascota, empleado, servicio, hora="10:00", estado="Programada"):
    """Cita de hoy creada directo (sin las validaciones de agenda), para probar la consulta del día."""
    from agenda.models import Cita

    inicio = en(hora, timezone.localdate())
    return Cita.objects.create(
        mascota=mascota,
        empleado=empleado,
        servicio=servicio,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=inicio + timedelta(minutes=servicio.duracion_min),
        estado=estado,
        motivo_cancelacion="Prueba" if estado == "Cancelada" else None,
    )


def paciente(nombre="Max", alergias=None):
    """Mascota con su expediente abierto (RD-10)."""
    from clinico.models import ExpedienteClinico

    animal = mascota(nombre)
    ExpedienteClinico.objects.create(mascota=animal, alergias=alergias)
    return animal
