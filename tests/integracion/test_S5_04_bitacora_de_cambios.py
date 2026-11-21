"""S5-04 · Los cambios en ventas, consultas, recetas e inventario quedan en la bitácora (RNF-03, Tabla 3.57).

Criterio del plan: la emisión de una receta, la firma, los ajustes, los cobros y las cancelaciones quedan
registrados, con la cuenta que los hizo y los valores previos cuando el registro ya existía.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from catalogos.models import CategoriaProducto, CategoriaServicio, Empleado, Puesto
from clinico import services as clinico
from inventario import services as inventario
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria
from tests import fabricas
from ventas import services as ventas
from ventas.services import Partida

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def _ultimo(entidad, accion=None):
    registros = BitacoraAuditoria.objects.filter(entidad=entidad)
    if accion:
        registros = registros.filter(accion=accion)
    return registros.order_by("-id_bitacora").first()


@pytest.fixture
def consulta_abierta():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    max_ = fabricas.paciente("Max")
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = clinico.abrir_consulta(cita, laura, {"sintomas": "Tos", "peso_kg": Decimal("20")})
    return laura, consulta


# --- Consultas, aplicaciones y recetas -------------------------------------------------
def test_S5_04_abrir_guardar_y_firmar_una_consulta_quedan_con_sus_valores_previos(consulta_abierta):
    laura, consulta = consulta_abierta
    alta = _ultimo("consulta", AccionBitacora.ALTA)
    assert (alta.id_registro, alta.usuario) == (consulta.pk, laura.usuario)

    datos = {"sintomas": "Tos seca", "peso_kg": Decimal("20.50"), "diagnostico": "Traqueítis"}
    clinico.guardar_consulta(consulta, laura, datos)
    cambio = _ultimo("consulta", AccionBitacora.MODIFICACION)
    previos = bitacora.valores_previos(cambio)
    assert previos["sintomas"] == "Tos" and previos["peso_kg"] == "20.00" and previos["diagnostico"] is None

    antes = BitacoraAuditoria.objects.count()
    clinico.guardar_consulta(consulta, laura, datos)  # sin cambios: no se registra nada
    assert BitacoraAuditoria.objects.count() == antes

    clinico.firmar(consulta, laura)
    firma = _ultimo("consulta", AccionBitacora.MODIFICACION)
    assert bitacora.valores_previos(firma)["estado"] == "Abierta"


def test_S5_04_aplicacion_quitada_y_receta_emitida(consulta_abierta):
    laura, consulta = consulta_abierta
    vacuna = fabricas.producto("VAC-B", "Vacuna B", stock_minimo=0)
    fabricas.lote(vacuna, 5, 200)
    proxima = timezone.localdate() + timedelta(days=365)
    (aplicada,) = clinico.registrar_aplicacion(consulta, laura, vacuna, 1, "1 mL", proxima)
    assert _ultimo("aplicacion", AccionBitacora.ALTA).id_registro == aplicada.pk

    clinico.quitar_aplicacion(aplicada, laura)
    quitada = _ultimo("aplicacion", AccionBitacora.CANCELACION)
    assert quitada.id_registro == aplicada.pk
    assert bitacora.valores_previos(quitada)["dosis"] == "1 mL"  # queda lo que se quitó

    medicamento = fabricas.producto("MED-B", "Amoxicilina", categoria=CategoriaProducto.MEDICAMENTO)
    receta = clinico.emitir_receta(consulta, laura, [(medicamento, "1 tableta", "Cada 12 h", 7, None)])
    emitida = _ultimo("receta", AccionBitacora.ALTA)
    assert (emitida.id_registro, emitida.usuario) == (receta.pk, laura.usuario)


def test_S5_04_atencion_de_estetica():
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    cita = fabricas.cita_de_hoy(
        fabricas.paciente("Canela"), mario, fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    )
    registro = clinico.registrar_estetica(cita, mario, {"estado_pelaje_piel": "Sano"})
    assert _ultimo("registro_estetica", AccionBitacora.ALTA).id_registro == registro.pk


# --- Inventario y compras -----------------------------------------------------------
def test_S5_04_entrada_y_ajuste_con_la_existencia_previa():
    admin = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Andrés")
    producto = fabricas.producto("ALI-B", "Croquetas", categoria=CategoriaProducto.ALIMENTO)
    lote = inventario.registrar_entrada(producto, "a-1", 10, admin, timezone.localdate() + timedelta(days=90))
    entrada = _ultimo("movimiento_inventario", AccionBitacora.ALTA)
    assert entrada.usuario == admin.usuario

    inventario.ajustar(lote, Decimal("-2"), "Conteo físico", admin)
    ajuste = _ultimo("lote", AccionBitacora.MODIFICACION)
    assert ajuste.id_registro == lote.pk
    assert bitacora.valores_previos(ajuste)["cantidad_disponible"] == "10.00"


def test_S5_04_pedido_creado_cambiado_recibido_y_cancelado():
    admin = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Andrés")
    proveedor = fabricas.proveedor()
    producto = fabricas.producto("ACC-B", "Collar", categoria=CategoriaProducto.ACCESORIO)
    pedido = inventario.guardar_pedido(proveedor, admin, [(producto, 5, Decimal("50"))])
    assert _ultimo("pedido_compra", AccionBitacora.ALTA).id_registro == pedido.pk

    inventario.guardar_pedido(proveedor, admin, [(producto, 8, Decimal("50"))], pedido=pedido)
    previos = bitacora.valores_previos(_ultimo("pedido_compra", AccionBitacora.MODIFICACION))
    assert previos["total"] == "250.00" and previos["partidas"] == [[producto.pk, 5, "50.00"]]

    detalle = pedido.detalles.get()
    inventario.recibir_pedido(pedido, admin, {detalle.pk: (8, "C-1", None)})
    recepcion = _ultimo("pedido_compra", AccionBitacora.MODIFICACION)
    assert bitacora.valores_previos(recepcion)["estado"] == "Pendiente"

    otro = inventario.guardar_pedido(proveedor, admin, [(producto, 1, Decimal("50"))])
    inventario.cancelar_pedido(otro, admin)
    cancelado = _ultimo("pedido_compra", AccionBitacora.CANCELACION)
    assert cancelado.id_registro == otro.pk and bitacora.valores_previos(cancelado)["estado"] == "Pendiente"


# --- Ventas -----------------------------------------------------------------------
def test_S5_04_ticket_cobro_y_factura():
    sofia = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Sofía")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    cliente = fabricas.paciente("Toby").cliente
    venta = ventas.generar_ticket(cliente, sofia, [Partida(servicio=bano)])
    assert _ultimo("venta", AccionBitacora.ALTA).id_registro == venta.pk

    pago = ventas.registrar_pago(venta, sofia, "Efectivo", Decimal("500"))
    cobro = _ultimo("pago", AccionBitacora.ALTA)
    assert (cobro.id_registro, cobro.usuario) == (pago.pk, sofia.usuario)

    cliente.rfc, cliente.regimen_fiscal, cliente.cp_fiscal = "LOAA800101AB1", "612", "89000"
    cliente.save()
    ventas.marcar_factura(venta, True, sofia.usuario)
    factura = _ultimo("venta", AccionBitacora.MODIFICACION)
    assert bitacora.valores_previos(factura) == {"requiere_factura": False}


# --- Reglas de la bitácora -----------------------------------------------------------
def test_S5_04_si_el_cambio_falla_no_queda_registro_y_sin_cuenta_no_hay_cambio():
    admin = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Andrés")
    producto = fabricas.producto("ALI-C", "Croquetas", categoria=CategoriaProducto.ALIMENTO)
    lote = fabricas.lote(producto, 1, 90)
    antes = BitacoraAuditoria.objects.count()
    with pytest.raises(inventario.ErrorInventario):
        inventario.ajustar(lote, Decimal("-5"), "Conteo físico", admin)
    assert BitacoraAuditoria.objects.count() == antes

    sin_cuenta = Empleado.objects.create(
        nombre="Sin", apellidos="Cuenta", puesto=Puesto.ADMINISTRADOR, fecha_ingreso=timezone.localdate()
    )
    with pytest.raises(RuntimeError, match="no tiene cuenta"):
        inventario.ajustar(lote, Decimal("1"), "Conteo físico", sin_cuenta)
    lote.refresh_from_db()
    assert lote.cantidad_disponible == Decimal("1")  # el ajuste se revirtió con la bitácora


def test_S5_04_la_base_no_deja_modificar_ni_borrar_la_bitacora():
    admin = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="Andrés")
    producto = fabricas.producto("ALI-D", "Croquetas", categoria=CategoriaProducto.ALIMENTO)
    inventario.registrar_entrada(producto, "D-1", 3, admin, timezone.localdate() + timedelta(days=90))
    registro = BitacoraAuditoria.objects.get()
    with pytest.raises(DatabaseError, match="RNF-03"), transaction.atomic():
        BitacoraAuditoria.objects.filter(pk=registro.pk).update(accion="Alta", entidad="otra")
    with pytest.raises(DatabaseError, match="RNF-03"), transaction.atomic():
        BitacoraAuditoria.objects.filter(pk=registro.pk).delete()
    assert BitacoraAuditoria.objects.get().entidad == "movimiento_inventario"
