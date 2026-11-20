"""S4-16 · Pruebas que intentan violar RD-06, RD-11, RD-12 y RF-14 por fuera del servicio de ventas.

El servicio valida antes de escribir (TU-10 a TU-12, TU-18); aquí se salta el servicio, como lo haría un
código futuro con QuerySet.update(), un create() directo o SQL, y se comprueba que la base de datos siga
protegiendo la regla (D-21, cambio 2026-11-20_RD-06_RD-11_RD-12_ventas.sql). Cada violación va en su propia
prueba: tras un error de SQL Server no se hacen más consultas.
"""

from decimal import Decimal

import pytest
from django.db import DatabaseError, IntegrityError, transaction

from catalogos.models import CategoriaProducto, CategoriaServicio, Puesto
from clinico.services import abrir_consulta, emitir_receta
from seguridad.models import Rol
from tests import fabricas
from ventas import services
from ventas.models import DetalleVenta, Pago, Venta
from ventas.services import Partida

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def venta(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)  # $400.00
    max_ = fabricas.paciente("Max")
    return (
        recepcion,
        services.generar_ticket(max_.cliente, recepcion.empleado, [Partida(servicio=bano)]),
        max_,
    )


# --- RD-06 · Pagos y cierre de venta ------------------------------------------------------
def test_S4_16_RD06_la_base_rechaza_un_saldo_negativo(venta):
    _, ticket, _ = venta
    with pytest.raises(IntegrityError, match="CK_venta_saldo"), transaction.atomic():
        Venta.objects.filter(pk=ticket.pk).update(saldo=Decimal("-50"))


def test_S4_16_RD06_la_base_rechaza_pagada_con_saldo(venta):
    _, ticket, _ = venta
    with pytest.raises(IntegrityError, match="CK_venta_pagada_saldo_cero"), transaction.atomic():
        Venta.objects.filter(pk=ticket.pk).update(estado="Pagada")


def test_S4_16_RD06_la_base_rechaza_un_cambio_que_no_cuadra(venta):
    recepcion, ticket, _ = venta
    with pytest.raises(IntegrityError, match="CK_pago_cambio"), transaction.atomic():
        Pago.objects.create(
            venta=ticket,
            empleado=recepcion.empleado,
            tipo="Abono",
            metodo="Efectivo",
            monto=Decimal("400"),
            monto_recibido=Decimal("500"),
            cambio=Decimal("50"),
        )


def test_S4_16_RD07_un_pago_no_se_modifica(venta):
    recepcion, ticket, _ = venta
    pago = services.registrar_pago(ticket, recepcion.empleado, "Efectivo", Decimal("400"))
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Pago.objects.filter(pk=pago.pk).update(monto=Decimal("1"))


def test_S4_16_RD07_un_pago_no_se_borra(venta):
    recepcion, ticket, _ = venta
    pago = services.registrar_pago(ticket, recepcion.empleado, "Tarjeta", Decimal("100"))
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Pago.objects.filter(pk=pago.pk).delete()


# --- RD-11 · Precio histórico --------------------------------------------------------------
def test_S4_16_RD11_la_linea_no_cambia_de_precio(venta):
    _, ticket, _ = venta
    with pytest.raises(DatabaseError, match="RD-11"), transaction.atomic():
        DetalleVenta.objects.filter(venta=ticket).update(precio_unitario=Decimal("1"), subtotal=Decimal("1"))


# --- RD-12 · Medicamento con control --------------------------------------------------------
@pytest.fixture
def amoxicilina():
    producto = fabricas.producto(
        "MED-001",
        "Amoxicilina",
        stock_minimo=0,
        categoria=CategoriaProducto.MEDICAMENTO,
        requiere_receta=True,
    )
    fabricas.lote(producto, 30, 200)
    return producto


def _linea(ticket, producto, receta=None):
    return DetalleVenta.objects.create(
        venta=ticket,
        numero_linea=2,
        producto=producto,
        receta=receta,
        cantidad=Decimal("1"),
        precio_unitario=producto.precio_venta,
        subtotal=producto.precio_venta,
    )


def test_S4_16_RD12_la_base_rechaza_el_medicamento_sin_receta(venta, amoxicilina):
    _, ticket, _ = venta
    with pytest.raises(IntegrityError, match="CK_detalle_venta_receta_valida"), transaction.atomic():
        _linea(ticket, amoxicilina)


def test_S4_16_RD12_la_base_rechaza_una_receta_que_no_lo_incluye(venta, amoxicilina):
    _, ticket, max_ = venta
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    otro = fabricas.producto("MED-002", "Meloxicam", stock_minimo=0, requiere_receta=True)
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = abrir_consulta(cita, laura, {"sintomas": "Dolor", "peso_kg": Decimal("28")})
    receta = emitir_receta(consulta, laura, [(otro, "1 mL", "Cada 24 horas", 3, None)])
    with pytest.raises(IntegrityError, match="CK_detalle_venta_receta_valida"), transaction.atomic():
        _linea(ticket, amoxicilina, receta)


def test_S4_16_RD12_con_la_receta_correcta_la_base_lo_acepta(venta, amoxicilina):
    _, ticket, max_ = venta
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = abrir_consulta(cita, laura, {"sintomas": "Otitis", "peso_kg": Decimal("28")})
    receta = emitir_receta(consulta, laura, [(amoxicilina, "1 tableta", "Cada 12 horas", 7, None)])
    assert _linea(ticket, amoxicilina, receta).pk


# --- RF-14 · Ticket cancelado en solo lectura ----------------------------------------------
def test_S4_16_RF14_un_ticket_cancelado_no_se_reactiva(venta):
    recepcion, ticket, _ = venta
    services.cancelar_venta(ticket, recepcion, "Prueba de solo lectura")
    with pytest.raises(DatabaseError, match="RF-14"), transaction.atomic():
        Venta.objects.filter(pk=ticket.pk).update(estado="Pendiente", motivo_cancelacion=None, cancelo=None)
