"""S0-14 · El esquema migrado coincide con el diccionario y la base protege las reglas (apartado 4.6.1).

Cada prueba de restricción intenta violar la regla directamente en la base, sin pasar por los servicios.
"""

from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, connection, transaction

from catalogos.models import Cliente, Empleado, HorarioLaboral, Producto, Puesto, Servicio
from inventario.models import Lote

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

TABLAS_DICCIONARIO = {
    "cliente",
    "especie",
    "raza",
    "mascota",
    "empleado",
    "horario_laboral",
    "usuario",
    "servicio",
    "cita",
    "expediente_clinico",
    "consulta",
    "aplicacion",
    "receta",
    "detalle_receta",
    "registro_estetica",
    "recordatorio",
    "producto",
    "lote",
    "movimiento_inventario",
    "proveedor",
    "pedido_compra",
    "detalle_pedido",
    "venta",
    "detalle_venta",
    "pago",
    "bitacora_auditoria",
}


def test_S0_existen_las_26_tablas_del_diccionario():
    assert len(TABLAS_DICCIONARIO) == 26
    tablas = set(connection.introspection.table_names())
    assert TABLAS_DICCIONARIO <= tablas, f"Faltan: {TABLAS_DICCIONARIO - tablas}"


def _viola(crear):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear()


def test_S0_base_rechaza_veterinario_sin_cedula():  # RF-03, RD-01
    _viola(
        lambda: Empleado.objects.create(
            nombre="Prueba", apellidos="Sin Cédula", puesto=Puesto.VETERINARIO, fecha_ingreso=date.today()
        )
    )


def test_S0_base_rechaza_cliente_sin_aviso_de_privacidad():  # RF-01, RNF-08
    _viola(
        lambda: Cliente.objects.create(
            nombre="Prueba",
            apellido_paterno="Sin Aviso",
            telefono="8330000000",
            preferencia_contacto="Teléfono",
            acepto_aviso_privacidad=False,
        )
    )


def test_S0_base_rechaza_valor_fuera_de_la_lista_permitida():
    _viola(
        lambda: Cliente.objects.create(
            nombre="Prueba",
            apellido_paterno="Canal",
            telefono="8330000000",
            preferencia_contacto="Paloma",
            acepto_aviso_privacidad=True,
        )
    )


def test_S0_base_rechaza_horario_con_salida_antes_de_entrada():  # RD-02
    empleado = Empleado.objects.create(
        nombre="Prueba", apellidos="Horario", puesto=Puesto.ESTILISTA, fecha_ingreso=date.today()
    )
    _viola(
        lambda: HorarioLaboral.objects.create(
            empleado=empleado, dia_semana=1, hora_entrada=time(19), hora_salida=time(9)
        )
    )


def test_S0_base_rechaza_estetica_asignada_a_veterinario():  # RD-04
    _viola(
        lambda: Servicio.objects.create(
            nombre="Baño",
            categoria="Estética",
            precio=Decimal("350"),
            duracion_min=60,
            puesto_requerido="Veterinario",
        )
    )


def test_S0_base_rechaza_existencias_negativas():  # RD-05
    producto = Producto.objects.create(
        codigo="PRB-001",
        nombre="Producto de prueba",
        categoria="Insumo",
        unidad_medida="Pieza",
        precio_venta=Decimal("10"),
    )
    _viola(
        lambda: Lote.objects.create(
            producto=producto,
            numero_lote="L1",
            fecha_caducidad=date.today() + timedelta(days=30),
            cantidad_disponible=-1,
        )
    )
