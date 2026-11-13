"""S0-14 · El esquema de bd/01_tablas.sql coincide con el diccionario y SQL Server protege las reglas.

Cada prueba de restricción intenta violar la regla directamente en la base, sin pasar por los servicios.
"""

from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.db import DatabaseError, IntegrityError, connection, transaction

from catalogos.models import Cliente, Empleado, HorarioLaboral, Producto, Puesto, Servicio
from inventario.models import Lote, MovimientoInventario, TipoMovimiento

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


def test_S0_cedula_unica_admite_varios_empleados_sin_cedula():  # D-12: índice único filtrado
    for nombre in ("Uno", "Dos"):
        Empleado.objects.create(
            nombre=nombre, apellidos="Sin Cédula", puesto=Puesto.ESTILISTA, fecha_ingreso=date.today()
        )
    Empleado.objects.create(
        nombre="Vet",
        apellidos="Uno",
        puesto=Puesto.VETERINARIO,
        cedula_profesional="CED123",
        fecha_ingreso=date.today(),
    )
    _viola(
        lambda: Empleado.objects.create(
            nombre="Vet",
            apellidos="Dos",
            puesto=Puesto.VETERINARIO,
            cedula_profesional="CED123",
            fecha_ingreso=date.today(),
        )
    )


def _producto_con_lotes():
    producto = Producto.objects.create(
        codigo="PRB-002",
        nombre="Vacuna de prueba",
        categoria="Vacuna",
        unidad_medida="Dosis",
        precio_venta=Decimal("100"),
        stock_minimo=10,
    )
    hoy = date.today()
    Lote.objects.create(
        producto=producto,
        numero_lote="VIGENTE",
        fecha_caducidad=hoy + timedelta(days=20),
        cantidad_disponible=6,
    )
    Lote.objects.create(
        producto=producto,
        numero_lote="VENCIDO",
        fecha_caducidad=hoy - timedelta(days=1),
        cantidad_disponible=50,
    )
    return producto


def test_S0_vista_stock_excluye_lotes_vencidos():  # RD-03, RD-05, RF-11
    producto = _producto_con_lotes()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT stock_disponible, bajo_minimo, caduca_en_30_dias FROM dbo.vista_stock_disponible "
            "WHERE id_producto = %s",
            [producto.id_producto],
        )
        stock, bajo_minimo, caduca_pronto = cursor.fetchone()
    assert stock == 6  # el lote vencido no cuenta
    assert bajo_minimo  # 6 < 10
    assert caduca_pronto  # el lote vigente caduca en 20 días


def test_S0_movimientos_de_inventario_no_se_modifican():  # RD-07, disparador
    producto = _producto_con_lotes()
    empleado = Empleado.objects.create(
        nombre="Admin", apellidos="Prueba", puesto=Puesto.ADMINISTRADOR, fecha_ingreso=date.today()
    )
    movimiento = MovimientoInventario.objects.create(
        lote=producto.lotes.first(), empleado=empleado, tipo=TipoMovimiento.ENTRADA, cantidad=6
    )
    with pytest.raises(DatabaseError), transaction.atomic():
        MovimientoInventario.objects.filter(pk=movimiento.pk).update(cantidad=60)
    with pytest.raises(DatabaseError), transaction.atomic():
        MovimientoInventario.objects.filter(pk=movimiento.pk).delete()
