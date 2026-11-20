"""S4-02 a S4-06 · Ventas: folio del ticket (D-20), generar el ticket (RF-13, RD-03, RD-05), precio
histórico (TU-12, RD-11), medicamento con control (TU-18, RD-12) y cobro de una cita (D-20, RD-09)."""

from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaProducto, CategoriaServicio, Puesto
from clinico.services import abrir_consulta, emitir_receta
from inventario.models import Lote, MovimientoInventario
from tests import fabricas
from ventas import services
from ventas.models import Venta
from ventas.services import Partida, siguiente_folio

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]


def test_S4_02_el_folio_es_consecutivo_y_reinicia_cada_ano():
    recepcion = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Sofía")
    cliente = fabricas.mascota().cliente
    assert siguiente_folio(date(2026, 11, 20)) == "T-2026-00001"
    for folio in ("T-2026-00001", "T-2026-00009", "T-2025-00040"):
        Venta.objects.create(folio_ticket=folio, cliente=cliente, empleado=recepcion)
    assert siguiente_folio(date(2026, 12, 31)) == "T-2026-00010"  # sigue al mayor del año
    assert siguiente_folio(date(2027, 1, 1)) == "T-2027-00001"  # cada año empieza en 1


# --- S4-04 a S4-06 · Generar el ticket ------------------------------------------------------


HOY = timezone.localdate()


@pytest.fixture
def mostrador():
    sofia = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Sofía")
    max_ = fabricas.paciente("Max")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    croquetas = fabricas.producto(
        "ALI-001",
        "Croquetas",
        stock_minimo=0,
        categoria=CategoriaProducto.ALIMENTO,
        precio_venta=Decimal("320"),
    )
    return sofia, max_.cliente, bano, croquetas, max_


def test_S4_04_el_ticket_descuenta_del_lote_que_caduca_primero_y_no_del_vencido(mostrador):
    sofia, cliente, bano, croquetas, _ = mostrador
    vencido = fabricas.lote(croquetas, 5, -1, numero="V")
    despues = fabricas.lote(croquetas, 5, 200, numero="B")
    antes = fabricas.lote(croquetas, 2, 30, numero="A")
    venta = services.generar_ticket(
        cliente, sofia, [Partida(producto=croquetas, cantidad=3), Partida(servicio=bano)]
    )

    assert venta.folio_ticket == f"T-{HOY:%Y}-00001" and venta.estado == "Pendiente"
    assert (venta.total, venta.saldo) == (Decimal("1360.00"), Decimal("1360.00"))  # 3 × 320 + 400
    existencias = {lote.numero_lote: lote.cantidad_disponible for lote in Lote.objects.all()}
    assert existencias == {"V": 5, "B": 4, "A": 0}  # RD-03 y RD-05
    assert vencido.pk and despues.pk and antes.pk
    referencias = set(MovimientoInventario.objects.filter(tipo="Venta").values_list("referencia", flat=True))
    assert referencias == {venta.folio_ticket}
    assert [linea.numero_linea for linea in venta.detalles.order_by("numero_linea")] == [1, 2]


def test_S4_04_sin_stock_suficiente_no_se_genera_nada(mostrador):
    sofia, cliente, bano, croquetas, _ = mostrador
    fabricas.lote(croquetas, 2, 100)
    with pytest.raises(services.ErrorVenta, match="Stock insuficiente: hay 2"):
        services.generar_ticket(
            cliente, sofia, [Partida(servicio=bano), Partida(producto=croquetas, cantidad=3)]
        )
    assert not Venta.objects.exists() and not MovimientoInventario.objects.filter(tipo="Venta").exists()
    assert Lote.objects.get().cantidad_disponible == 2


@pytest.mark.parametrize(
    "partidas, mensaje",
    [
        ([], "Agregue al menos un producto o servicio"),
        ([("bano", 1), ("bano", 2)], "aparece dos veces"),
        ([("bano", "1.5")], "se cobra por unidad"),
        ([("croquetas", "0.001")], "hasta 2 decimales"),
    ],
)
def test_S4_04_lineas_que_no_se_aceptan(mostrador, partidas, mensaje):
    sofia, cliente, bano, croquetas, _ = mostrador
    fabricas.lote(croquetas, 10, 100)
    articulos = {"bano": {"servicio": bano}, "croquetas": {"producto": croquetas}}
    lineas = [Partida(**articulos[nombre], cantidad=Decimal(str(c))) for nombre, c in partidas]
    with pytest.raises(services.ErrorVenta, match=mensaje):
        services.generar_ticket(cliente, sofia, lineas)


def test_S4_04_un_cliente_dado_de_baja_no_compra(mostrador):
    sofia, cliente, bano, *_ = mostrador
    cliente.activo = False
    cliente.save()
    with pytest.raises(services.ErrorVenta, match="dado de baja"):
        services.generar_ticket(cliente, sofia, [Partida(servicio=bano)])


def test_TU12_el_ticket_conserva_el_precio_aunque_suba_el_servicio(mostrador):
    """TU-12 · RD-11: se genera un ticket y después sube el precio del servicio; el ticket no cambia."""
    sofia, cliente, bano, *_ = mostrador
    venta = services.generar_ticket(cliente, sofia, [Partida(servicio=bano)])
    bano.precio = Decimal("500.00")
    bano.save()
    linea = venta.detalles.get()
    assert (linea.precio_unitario, linea.subtotal) == (Decimal("400.00"), Decimal("400.00"))
    venta.refresh_from_db()
    assert venta.total == Decimal("400.00")
    otra = services.generar_ticket(cliente, sofia, [Partida(servicio=bano)])
    assert otra.detalles.get().precio_unitario == Decimal("500.00")  # el siguiente toma el precio nuevo


# --- S4-06 · RD-12: medicamento con control ------------------------------------------------
@pytest.fixture
def con_receta(mostrador):
    sofia, cliente, bano, croquetas, max_ = mostrador
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    amoxicilina = fabricas.producto(
        "MED-001",
        "Amoxicilina",
        stock_minimo=0,
        categoria=CategoriaProducto.MEDICAMENTO,
        requiere_receta=True,
    )
    fabricas.lote(amoxicilina, 30, 200)
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = abrir_consulta(cita, laura, {"sintomas": "Otitis", "peso_kg": Decimal("28")})
    receta = emitir_receta(consulta, laura, [(amoxicilina, "1 tableta", "Cada 12 horas", 7, None)])
    return sofia, cliente, amoxicilina, receta, croquetas


def test_TU18_sin_folio_no_se_agrega_y_con_folio_valido_si(con_receta):
    """TU-18 · RD-12: un medicamento que requiere receta sin folio no se agrega; con folio válido, sí."""
    sofia, cliente, amoxicilina, receta, _ = con_receta
    with pytest.raises(services.ErrorVenta, match="requiere receta: capture el folio"):
        services.generar_ticket(cliente, sofia, [Partida(producto=amoxicilina, cantidad=14)])
    assert not Venta.objects.exists()
    venta = services.generar_ticket(
        cliente, sofia, [Partida(producto=amoxicilina, cantidad=14, folio_receta=receta.folio.lower())]
    )
    assert venta.detalles.get().receta == receta


def test_TU18_el_folio_debe_existir_ser_del_cliente_e_incluir_el_producto(con_receta):
    sofia, cliente, amoxicilina, receta, croquetas = con_receta
    meloxicam = fabricas.producto("MED-002", "Meloxicam", stock_minimo=0, requiere_receta=True)
    fabricas.lote(meloxicam, 5, 200)
    with pytest.raises(services.ErrorVenta, match="No existe la receta R-2026-99999"):
        services.generar_ticket(
            cliente, sofia, [Partida(producto=amoxicilina, cantidad=1, folio_receta="R-2026-99999")]
        )
    with pytest.raises(services.ErrorVenta, match="no incluye «Meloxicam»"):
        services.generar_ticket(
            cliente, sofia, [Partida(producto=meloxicam, cantidad=1, folio_receta=receta.folio)]
        )
    otro = fabricas.mascota("Firulais", cliente_nombre="Pedro").cliente
    with pytest.raises(services.ErrorVenta, match="es de una mascota de otro cliente"):
        services.generar_ticket(
            otro, sofia, [Partida(producto=amoxicilina, cantidad=1, folio_receta=receta.folio)]
        )


# --- S4-05 · Ticket desde una cita (D-20) -------------------------------------------------
def test_S4_05_la_cita_propone_su_servicio_y_el_cobro_de_lo_aplicado(mostrador):
    sofia, cliente, _, _, max_ = mostrador
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    cobro = fabricas.servicio("Aplicación de vacuna", CategoriaServicio.APLICACION, 10)
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    aplicada = fabricas.aplicacion(max_, laura, vacuna, 365)
    cita = aplicada.consulta.cita
    Cita.objects.filter(pk=cita.pk).update(estado=EstadoCita.COMPLETADA)
    cita.refresh_from_db()

    assert list(services.citas_por_cobrar()) == [cita]
    propuesta = services.partidas_de_la_cita(cita)
    assert [p.servicio for p in propuesta] == [cita.servicio, cobro]
    venta = services.generar_ticket(cliente, sofia, propuesta, cita=cita)
    assert venta.cita == cita and venta.total == Decimal("800.00")
    assert not MovimientoInventario.objects.filter(tipo="Venta").exists()  # RD-09: no vuelve a bajar
    assert list(services.citas_por_cobrar()) == []
    with pytest.raises(services.ErrorVenta, match=f"ya se cobró en el ticket {venta.folio_ticket}"):
        services.generar_ticket(cliente, sofia, propuesta, cita=cita)


def test_S4_05_la_cita_debe_ser_del_cliente(mostrador):
    sofia, _, bano, _, max_ = mostrador
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    cita = fabricas.cita_de_hoy(max_, mario, bano, estado="Completada")
    otro = fabricas.mascota("Firulais", cliente_nombre="Pedro").cliente
    with pytest.raises(services.ErrorVenta, match="otro cliente"):
        services.generar_ticket(otro, sofia, [Partida(servicio=bano)], cita=cita)


# --- S4-08 · Pagos (RD-06, TU-10, TU-11) --------------------------------------------------
@pytest.fixture
def ticket_de_350(mostrador):
    sofia, cliente, bano, *_ = mostrador
    bano.precio = Decimal("350.00")
    bano.save()
    return sofia, services.generar_ticket(cliente, sofia, [Partida(servicio=bano)])


def test_TU10_el_pago_en_efectivo_no_excede_el_saldo_y_calcula_el_cambio(ticket_de_350):
    """TU-10 · RD-06: saldo de $350 y pago de $500 en efectivo → se registran $350 y un cambio de $150."""
    sofia, venta = ticket_de_350
    pago = services.registrar_pago(venta, sofia, "Efectivo", Decimal("500"))
    assert (pago.monto, pago.monto_recibido, pago.cambio) == (
        Decimal("350.00"),
        Decimal("500"),
        Decimal("150"),
    )
    venta.refresh_from_db()
    assert (venta.estado, venta.saldo) == ("Pagada", Decimal("0.00"))


def test_TU11_dos_abonos_hasta_saldo_cero(ticket_de_350):
    """TU-11 · RF-13, RD-06: total de $350; abono de $200 y después de $150."""
    sofia, venta = ticket_de_350
    services.registrar_pago(venta, sofia, "Tarjeta", Decimal("200"), "AUT 123456")
    venta.refresh_from_db()
    assert (venta.estado, venta.saldo) == ("Pendiente", Decimal("150.00"))
    pago = services.registrar_pago(venta, sofia, "Transferencia", Decimal("150"))
    assert (pago.monto_recibido, pago.cambio) == (None, None)  # sin efectivo no hay cambio
    venta.refresh_from_db()
    assert (venta.estado, venta.saldo) == ("Pagada", Decimal("0.00"))
    with pytest.raises(services.ErrorVenta, match="ya está pagado"):
        services.registrar_pago(venta, sofia, "Efectivo", Decimal("10"))


@pytest.mark.parametrize(
    "metodo, monto, mensaje",
    [
        ("Tarjeta", "351", "se cobra como máximo el saldo"),
        ("Cheque", "100", "Elija el método de pago"),
        ("Efectivo", "0", "mayor que cero"),
        ("Efectivo", "10.005", "hasta 2 decimales"),
    ],
)
def test_S4_08_pagos_que_no_se_aceptan(ticket_de_350, metodo, monto, mensaje):
    sofia, venta = ticket_de_350
    with pytest.raises(services.ErrorVenta, match=mensaje):
        services.registrar_pago(venta, sofia, metodo, Decimal(monto))
    venta.refresh_from_db()
    assert venta.saldo == Decimal("350.00") and not venta.pagos.exists()


def test_S4_09_requiere_factura_solo_con_datos_fiscales(ticket_de_350):
    _, venta = ticket_de_350
    with pytest.raises(
        services.ErrorVenta, match="capture en la ficha de .*: RFC, régimen fiscal, código postal"
    ):
        services.marcar_factura(venta, True)
    cliente = venta.cliente
    cliente.rfc, cliente.regimen_fiscal, cliente.cp_fiscal = "LOAA800101AB1", "612", "89000"
    cliente.save()
    assert services.marcar_factura(venta, True).requiere_factura
    assert not services.marcar_factura(venta, False).requiere_factura


# --- S4-11 y S4-12 · Cancelación (RF-14, RNF-03) -----------------------------------------
@pytest.fixture
def venta_con_producto(mostrador, crear_usuario):
    from seguridad.models import Rol

    _, cliente, bano, croquetas, _ = mostrador
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    fabricas.lote(croquetas, 3, 30, numero="A")
    fabricas.lote(croquetas, 10, 200, numero="B")
    venta = services.generar_ticket(
        cliente, recepcion.empleado, [Partida(producto=croquetas, cantidad=5), Partida(servicio=bano)]
    )  # toma 3 del lote A y 2 del B; total 5 × 320 + 400 = 2,000
    return recepcion, admin, venta


def _existencias():
    return {lote.numero_lote: lote.cantidad_disponible for lote in Lote.objects.all()}


def test_S4_11_la_recepcionista_cancela_un_ticket_sin_pagos_y_regresa_lo_vendido(venta_con_producto):
    from seguridad.models import AccionBitacora, BitacoraAuditoria

    recepcion, _, venta = venta_con_producto
    assert _existencias() == {"A": 0, "B": 8}
    with pytest.raises(services.ErrorVenta, match="Escriba el motivo"):
        services.cancelar_venta(venta, recepcion, "   ")

    cancelada = services.cancelar_venta(venta, recepcion, "El cliente se arrepintió")
    assert (cancelada.estado, cancelada.motivo_cancelacion) == ("Cancelada", "El cliente se arrepintió")
    assert cancelada.cancelo == recepcion.empleado
    assert _existencias() == {"A": 3, "B": 10}  # cada pieza regresa a su lote
    devoluciones = MovimientoInventario.objects.filter(tipo="Devolución").order_by("id_movimiento")
    assert [(m.lote.numero_lote, m.cantidad) for m in devoluciones] == [("A", 3), ("B", 2)]
    assert {m.referencia for m in devoluciones} == {f"Cancelación {venta.folio_ticket}"}
    registro = BitacoraAuditoria.objects.get()
    assert (registro.accion, registro.entidad, registro.id_registro) == (
        AccionBitacora.CANCELACION,
        "venta",
        venta.pk,
    )
    with pytest.raises(services.ErrorVenta, match="ya está cancelado"):
        services.cancelar_venta(venta, recepcion, "Otra vez")
    with pytest.raises(services.ErrorVenta, match="está cancelado; no recibe pagos"):
        services.registrar_pago(venta, recepcion.empleado, "Efectivo", Decimal("10"))


def test_S4_12_con_pagos_solo_el_administrador_cancela_y_devuelve_por_metodo(venta_con_producto):
    from django.core.exceptions import PermissionDenied

    from seguridad import bitacora
    from seguridad.models import BitacoraAuditoria

    recepcion, admin, venta = venta_con_producto
    services.registrar_pago(venta, recepcion.empleado, "Tarjeta", Decimal("500"))
    services.registrar_pago(venta, recepcion.empleado, "Efectivo", Decimal("700"))
    assert not services.puede_cancelar(recepcion, venta) and services.puede_cancelar(admin, venta)
    with pytest.raises(PermissionDenied, match="Solo el Administrador"):
        services.cancelar_venta(venta, recepcion, "Error de captura")
    assert Venta.objects.get(pk=venta.pk).estado == "Pendiente" and _existencias() == {"A": 0, "B": 8}

    cancelada = services.cancelar_venta(venta, admin, "Error de captura")
    devoluciones = cancelada.pagos.filter(tipo="Devolución").order_by("metodo")
    assert [(p.metodo, p.monto) for p in devoluciones] == [
        ("Efectivo", Decimal("700.00")),
        ("Tarjeta", Decimal("500.00")),
    ]
    assert services.abonado(cancelada) == 0 and cancelada.saldo == cancelada.total
    assert _existencias() == {"A": 3, "B": 10}
    previos = bitacora.valores_previos(BitacoraAuditoria.objects.get())
    assert previos["estado"] == "Pendiente" and previos["saldo"] == "800.00"  # valores antes de cancelar


def test_S4_12_lo_aplicado_y_cobrado_con_servicio_no_regresa_y_la_cita_vuelve_a_cobrarse(
    mostrador, crear_usuario
):
    from seguridad.models import Rol

    _, cliente, _, _, max_ = mostrador
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    fabricas.servicio("Aplicación de vacuna", CategoriaServicio.APLICACION, 10)
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    cita = fabricas.aplicacion(max_, laura, vacuna, 365).consulta.cita
    Cita.objects.filter(pk=cita.pk).update(estado=EstadoCita.COMPLETADA)
    cita.refresh_from_db()
    venta = services.generar_ticket(cliente, admin.empleado, services.partidas_de_la_cita(cita), cita=cita)
    services.registrar_pago(venta, admin.empleado, "Efectivo", venta.total)

    services.cancelar_venta(venta, admin, "Cobro duplicado")
    assert Lote.objects.get(producto=vacuna).cantidad_disponible == 19  # la vacuna ya está en la mascota
    assert not MovimientoInventario.objects.filter(tipo="Devolución").exists()
    assert list(services.citas_por_cobrar()) == [cita]  # se puede volver a cobrar bien
