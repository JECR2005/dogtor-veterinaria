"""Servicios (reglas de negocio) del componente «Ventas y caja».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P4:

- RF-13, RD-06 y RD-11: tickets, pagos parciales con cambio, precio histórico y corte de caja (P4).
- RD-12: producto con control solo con folio de receta válido (P4).
- RF-14: cancelación con permisos según haya pagos; reintegro de productos vendidos (P4).

D-20: el folio del ticket es consecutivo por año, T-AAAA-NNNNN (como el de las recetas); lo aplicado en
consulta se cobra con un servicio de la categoría Aplicación y no vuelve a descontar el lote (RD-09).
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import Servicio
from clinico.models import Aplicacion, Receta, TipoAplicacion
from inventario import services as inventario
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from seguridad import bitacora
from seguridad.bitacora import valores_de
from seguridad.models import AccionBitacora

from .models import DetalleVenta, EstadoVenta, MetodoPago, Pago, TipoPago, Venta

PREFIJO_FOLIO = "T"


def siguiente_folio(hoy=None):
    """D-20 · Siguiente folio del año: T-2026-00001, T-2026-00002…

    Se toma dentro de la transacción del ticket; si dos tickets tomaran el mismo a la vez,
    UQ_venta_folio_ticket rechaza el segundo y se reintenta.
    """
    hoy = hoy or timezone.localdate()
    prefijo = f"{PREFIJO_FOLIO}-{hoy:%Y}-"
    ultimos = Venta.objects.filter(folio_ticket__startswith=prefijo).values_list("folio_ticket", flat=True)
    numero = max((int(folio.rsplit("-", 1)[1]) for folio in ultimos), default=0) + 1
    return f"{prefijo}{numero:05d}"


class ErrorVenta(Exception):
    """Operación de venta rechazada; el mensaje dice qué ocurrió y qué hacer (RI-08)."""


# D-20 · Servicio con el que se cobra cada tipo de aplicación (RD-09: no vuelve a descontar el lote)
SERVICIO_POR_APLICACION = {
    TipoAplicacion.VACUNA: "Aplicación de vacuna",
    TipoAplicacion.DESPARASITANTE: "Aplicación de desparasitante",
}
CENTAVO = Decimal("0.01")


@dataclass
class Partida:
    """Una línea del ticket antes de generarlo: un producto o un servicio, con su cantidad."""

    producto: object = None
    servicio: object = None
    cantidad: Decimal = Decimal("1")
    folio_receta: str = ""

    @property
    def articulo(self):
        return self.producto or self.servicio


# --- S4-05 · Ticket desde una cita (TI-05) ----------------------------------------------
def venta_de_la_cita(cita):
    """El ticket vigente (no cancelado) de una cita, si ya se cobró."""
    return Venta.objects.filter(cita=cita).exclude(estado=EstadoVenta.CANCELADA).first()


def partidas_de_la_cita(cita):
    """D-20 · Lo que se propone cobrar de una cita: su servicio y un servicio de cobro por cada aplicación."""
    partidas = [Partida(servicio=cita.servicio)]
    servicios = {
        s.nombre: s for s in Servicio.objects.filter(activo=True, nombre__in=SERVICIO_POR_APLICACION.values())
    }
    aplicaciones = Aplicacion.objects.filter(consulta__cita=cita).order_by("id_aplicacion")
    vistas = set()
    for aplicacion in aplicaciones:
        clave = (aplicacion.lote.producto_id, aplicacion.tipo)
        servicio = servicios.get(SERVICIO_POR_APLICACION.get(aplicacion.tipo))
        if servicio is None or clave in vistas:  # una dosis tomada de dos lotes se cobra una vez
            continue
        vistas.add(clave)
        partidas.append(Partida(servicio=servicio))
    return partidas


def citas_por_cobrar(hoy=None):
    """Citas completadas del día que todavía no tienen ticket (UI-17, lista de tickets)."""
    hoy = hoy or timezone.localdate()
    inicio = timezone.make_aware(datetime.combine(hoy, time.min))
    cobradas = (
        Venta.objects.exclude(estado=EstadoVenta.CANCELADA).filter(cita__isnull=False).values("cita_id")
    )
    return (
        Cita.objects.filter(
            estado=EstadoCita.COMPLETADA,
            fecha_hora_inicio__gte=inicio,
            fecha_hora_inicio__lt=inicio + timedelta(days=1),
        )
        .exclude(pk__in=cobradas)
        .select_related("mascota__cliente", "servicio", "empleado")
        .order_by("fecha_hora_inicio")
    )


# --- S4-06 · Medicamento con control (RD-12, TU-18, TI-07) -------------------------------
def receta_para(producto, folio, cliente):
    """La receta del folio, si es de una mascota del cliente e incluye el producto; si no, ErrorVenta."""
    folio = (folio or "").strip().upper()
    if not folio:
        raise ErrorVenta(f"«{producto.nombre}» requiere receta: capture el folio de la receta (RD-12).")
    receta = Receta.objects.select_related("consulta__expediente__mascota").filter(folio=folio).first()
    if receta is None:
        raise ErrorVenta(f"No existe la receta {folio}. Revise el folio.")
    if receta.consulta.expediente.mascota.cliente_id != cliente.pk:
        raise ErrorVenta(f"La receta {folio} es de una mascota de otro cliente.")
    if not receta.detalles.filter(producto=producto).exists():
        raise ErrorVenta(f"La receta {folio} no incluye «{producto.nombre}».")
    return receta


# --- S4-04 · Generar el ticket (RF-13, RD-03, RD-05, RD-11) -------------------------------
def generar_ticket(cliente, empleado, partidas, cita=None, hoy=None):
    """Genera el ticket con sus líneas a precio vigente (RD-11) y descuenta los productos vendidos.

    El stock baja al generar el ticket, del lote que caduca primero y nunca de uno vencido (RF-13, RD-03,
    RD-05). Los servicios, incluidos los de cobro de una aplicación, no tocan el inventario (RD-09).
    Todo o nada: si una línea no se puede vender, no se genera el ticket.
    """
    hoy = hoy or timezone.localdate()
    partidas = [p for p in partidas if p.articulo is not None]
    if not partidas:
        raise ErrorVenta("Agregue al menos un producto o servicio al ticket.")
    if not cliente.activo:
        raise ErrorVenta("El cliente está dado de baja; no se le pueden generar tickets.")
    productos = [p.producto.pk for p in partidas if p.producto]
    servicios = [p.servicio.pk for p in partidas if p.servicio]
    if len(productos) != len(set(productos)) or len(servicios) != len(set(servicios)):
        raise ErrorVenta("Un producto o servicio aparece dos veces; junte las cantidades en una sola línea.")
    for partida in partidas:
        partida.cantidad = Decimal(str(partida.cantidad))
        if partida.cantidad <= 0 or partida.cantidad != partida.cantidad.quantize(CENTAVO):
            raise ErrorVenta(
                f"Revise la cantidad de «{partida.articulo.nombre}»: mayor que cero, hasta 2 decimales."
            )
        if partida.servicio and partida.cantidad != partida.cantidad.to_integral_value():
            raise ErrorVenta(f"«{partida.servicio.nombre}» se cobra por unidad: use una cantidad entera.")
        if not partida.articulo.activo:
            raise ErrorVenta(f"«{partida.articulo.nombre}» ya no se ofrece.")
        partida.receta = None
        if partida.producto and partida.producto.requiere_receta:
            partida.receta = receta_para(partida.producto, partida.folio_receta, cliente)
    if cita is not None:
        if cita.mascota.cliente_id != cliente.pk:
            raise ErrorVenta("La cita es de una mascota de otro cliente.")
        if cita.estado == EstadoCita.CANCELADA:
            raise ErrorVenta("La cita está cancelada; no se cobra.")

    for intento in range(3):  # el folio es único: si dos tickets toman el mismo a la vez, se reintenta
        try:
            with transaction.atomic():
                return _crear(cliente, empleado, partidas, cita, hoy)
        except IntegrityError:
            if intento == 2:
                raise
    return None  # pragma: no cover


def _crear(cliente, empleado, partidas, cita, hoy):
    if cita is not None:
        Cita.objects.select_for_update().filter(pk=cita.pk).first()
        anterior = venta_de_la_cita(cita)
        if anterior:
            raise ErrorVenta(f"La cita ya se cobró en el ticket {anterior.folio_ticket}.")
    venta = Venta.objects.create(
        folio_ticket=siguiente_folio(hoy), cliente=cliente, empleado=empleado, cita=cita
    )
    total = Decimal("0")
    for numero, partida in enumerate(partidas, start=1):
        precio = Decimal(str(partida.producto.precio_venta if partida.producto else partida.servicio.precio))
        if partida.producto:
            try:
                inventario.descontar(
                    partida.producto, partida.cantidad, empleado, TipoMovimiento.VENTA, venta.folio_ticket
                )
            except inventario.ErrorInventario as error:
                raise ErrorVenta(str(error)) from error
        subtotal = (precio * partida.cantidad).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        DetalleVenta.objects.create(
            venta=venta,
            numero_linea=numero,
            producto=partida.producto,
            servicio=partida.servicio,
            receta=partida.receta,
            cantidad=partida.cantidad,
            precio_unitario=precio,  # RD-11: el precio queda fijo en la línea
            subtotal=subtotal,
        )
        total += subtotal
    venta.total = venta.saldo = total
    venta.estado = EstadoVenta.PAGADA if total == 0 else EstadoVenta.PENDIENTE
    venta.save(update_fields=["total", "saldo", "estado"])
    return venta


# --- S4-07 · Lista de tickets ---------------------------------------------------------------
def tickets(dia=None, estado=""):
    """Tickets de un día, del más reciente al más antiguo, con su cliente."""
    dia = dia or timezone.localdate()
    inicio = timezone.make_aware(datetime.combine(dia, time.min))
    lista = Venta.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=inicio + timedelta(days=1))
    if estado:
        lista = lista.filter(estado=estado)
    return lista.select_related("cliente", "empleado", "cita__mascota").order_by("-fecha_hora")


# --- S4-08 · Pagos parciales con cambio (RF-13, RD-06, TU-10, TU-11) ------------------------
def registrar_pago(venta, empleado, metodo, recibido, referencia=None):
    """Registra un abono. El monto aplicado es el menor entre lo recibido y el saldo (RD-06).

    - Efectivo: si se recibe más que el saldo, se aplica el saldo y el cambio es la diferencia (TU-10).
    - Tarjeta o transferencia: se cobra exactamente lo que se carga, sin cambio, como máximo el saldo.
    El ticket pasa a «Pagada» solo cuando el saldo llega a cero (TU-11, CK_venta_pagada_saldo_cero).
    """
    if metodo not in MetodoPago.values:
        raise ErrorVenta("Elija el método de pago: efectivo, tarjeta o transferencia.")
    try:
        recibido = Decimal(str(recibido))
    except (ArithmeticError, ValueError) as error:
        raise ErrorVenta("Capture el monto con números, por ejemplo 350.00.") from error
    if recibido <= 0 or recibido != recibido.quantize(CENTAVO):
        raise ErrorVenta("El monto debe ser mayor que cero y con hasta 2 decimales.")
    referencia = " ".join((referencia or "").split())[:40] or None
    with transaction.atomic():
        actual = Venta.objects.select_for_update().get(pk=venta.pk)  # un pago a la vez por ticket
        if actual.estado == EstadoVenta.PAGADA:
            raise ErrorVenta(f"El ticket {actual.folio_ticket} ya está pagado.")
        if actual.estado == EstadoVenta.CANCELADA:
            raise ErrorVenta(f"El ticket {actual.folio_ticket} está cancelado; no recibe pagos.")
        efectivo = metodo == MetodoPago.EFECTIVO
        if not efectivo and recibido > actual.saldo:
            raise ErrorVenta(
                f"Con {metodo.lower()} se cobra como máximo el saldo ({_pesos(actual.saldo)}); "
                "no hay cambio que devolver."
            )
        monto = min(recibido, actual.saldo)
        pago = Pago.objects.create(
            venta=actual,
            empleado=empleado,
            tipo=TipoPago.ABONO,
            metodo=metodo,
            monto=monto,
            monto_recibido=recibido if efectivo else None,
            cambio=recibido - monto if efectivo else None,
            referencia=referencia,
        )
        actual.saldo -= monto
        actual.estado = EstadoVenta.PAGADA if actual.saldo == 0 else EstadoVenta.PENDIENTE
        actual.save(update_fields=["saldo", "estado"])
    return pago


def _pesos(valor):
    from catalogos.templatetags.formato import pesos

    return pesos(valor)


# --- S4-09 · Requiere factura (RF-13, R11) -----------------------------------------------
def datos_fiscales_faltantes(cliente):
    """Lo que falta en la ficha del cliente para facturar: la factura se emite fuera del sistema (RF-13)."""
    faltan = []
    if not (cliente.rfc or "").strip():
        faltan.append("RFC")
    if not (cliente.regimen_fiscal or "").strip():
        faltan.append("régimen fiscal")
    if not (cliente.cp_fiscal or "").strip():
        faltan.append("código postal fiscal")
    return faltan


def marcar_factura(venta, requiere):
    """Marca o desmarca «Requiere factura». Solo con los datos fiscales completos del cliente."""
    with transaction.atomic():
        actual = Venta.objects.select_for_update().select_related("cliente").get(pk=venta.pk)
        if actual.estado == EstadoVenta.CANCELADA:
            raise ErrorVenta(f"El ticket {actual.folio_ticket} está cancelado.")
        if requiere:
            faltan = datos_fiscales_faltantes(actual.cliente)
            if faltan:
                raise ErrorVenta(
                    f"Para facturar, capture en la ficha de {actual.cliente}: {', '.join(faltan)}."
                )
        actual.requiere_factura = bool(requiere)
        actual.save(update_fields=["requiere_factura"])
    return actual


# --- S4-11 y S4-12 · Cancelación (RF-14, RNF-03, TI-06, adelanto de TI-09) ------------------
MOTIVO_MAXIMO = 150


def abonado(venta):
    """Lo que el cliente ha pagado del ticket: abonos menos devoluciones."""
    pagos = {t: Decimal("0") for t in TipoPago.values}
    for tipo, monto in venta.pagos.values_list("tipo", "monto"):
        pagos[tipo] += monto
    return pagos[TipoPago.ABONO] - pagos[TipoPago.DEVOLUCION]


def puede_cancelar(usuario, venta):
    """RF-14: la Recepcionista cancela tickets sin pagos; con pagos, solo el Administrador."""
    from seguridad.models import Rol

    if venta.estado == EstadoVenta.CANCELADA:
        return False
    return usuario.rol == Rol.ADMINISTRADOR or abonado(venta) == 0


def resumen_cancelacion(venta):
    """UI-18 · Lo que pasará al cancelar: devoluciones por método y productos que regresan a su lote.

    Solo regresan los productos vendidos en el ticket (sus movimientos «Venta»); lo aplicado a una mascota y
    cobrado con un servicio no cambia (RF-14, RD-09).
    """
    devoluciones = {}
    for metodo, tipo, monto in venta.pagos.values_list("metodo", "tipo", "monto"):
        signo = 1 if tipo == TipoPago.ABONO else -1
        devoluciones[metodo] = devoluciones.get(metodo, Decimal("0")) + signo * monto
    vendidos = (
        MovimientoInventario.objects.filter(tipo=TipoMovimiento.VENTA, referencia=venta.folio_ticket)
        .select_related("lote__producto")
        .order_by("id_movimiento")
    )
    return {
        "devoluciones": [(metodo, monto) for metodo, monto in devoluciones.items() if monto > 0],
        "reintegros": [(m.lote, -m.cantidad) for m in vendidos],
        "servicios": [d for d in venta.detalles.select_related("servicio") if d.servicio_id],
    }


def cancelar_venta(venta, usuario, motivo):
    """Cancela el ticket: devolución de lo abonado, reintegro de lo vendido y registro en la bitácora."""
    motivo = " ".join((motivo or "").split())
    if not motivo:
        raise ErrorVenta("Escriba el motivo de la cancelación.")
    if len(motivo) > MOTIVO_MAXIMO:
        raise ErrorVenta(f"El motivo admite hasta {MOTIVO_MAXIMO} caracteres.")
    with transaction.atomic():
        actual = Venta.objects.select_for_update().get(pk=venta.pk)
        if actual.estado == EstadoVenta.CANCELADA:
            raise ErrorVenta(f"El ticket {actual.folio_ticket} ya está cancelado.")
        if not puede_cancelar(usuario, actual):
            raise PermissionDenied("Solo el Administrador cancela un ticket con pagos (RF-14).")
        previos = valores_de(actual)
        resumen = resumen_cancelacion(actual)
        referencia = f"Cancelación {actual.folio_ticket}"
        for lote, cantidad in resumen["reintegros"]:  # vuelve al mismo lote del que salió
            Lote.objects.filter(pk=lote.pk).update(cantidad_disponible=F("cantidad_disponible") + cantidad)
            MovimientoInventario.objects.create(
                lote=lote,
                empleado=usuario.empleado,
                tipo=TipoMovimiento.DEVOLUCION,
                cantidad=cantidad,
                referencia=referencia,
            )
        for metodo, monto in resumen["devoluciones"]:
            Pago.objects.create(
                venta=actual,
                empleado=usuario.empleado,
                tipo=TipoPago.DEVOLUCION,
                metodo=metodo,
                monto=monto,
                referencia=referencia,
            )
        actual.estado = EstadoVenta.CANCELADA
        actual.motivo_cancelacion = motivo
        actual.cancelo = usuario.empleado
        actual.saldo = actual.total  # ya no se debe nada ni se conserva nada de lo pagado
        actual.save(update_fields=["estado", "motivo_cancelacion", "cancelo", "saldo"])
        bitacora.registrar(usuario, AccionBitacora.CANCELACION, actual, previos)  # RNF-03
    return actual


# --- S4-13 y S4-14 · Corte de caja (RF-13, TI-12) -------------------------------------------
def corte_de_caja(dia=None):
    """UI-19 · Pagos y devoluciones del día por método; el neto es lo que debe haber en caja o en banco.

    Cuenta por la fecha del pago (no la del ticket): un abono de hoy a un ticket de ayer entra en el corte de
    hoy. En efectivo además se muestra lo recibido y el cambio entregado: recibido − cambio = abonos.
    """
    dia = dia or timezone.localdate()
    inicio = timezone.make_aware(datetime.combine(dia, time.min))
    pagos = list(
        Pago.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=inicio + timedelta(days=1))
        .select_related("venta__cliente", "empleado")
        .order_by("fecha_hora", "id_pago")
    )
    cero = Decimal("0.00")
    metodos = {
        m: {"metodo": m, "abonos": cero, "devoluciones": cero, "recibido": cero, "cambio": cero, "pagos": 0}
        for m in MetodoPago.values
    }
    for pago in pagos:
        fila = metodos[pago.metodo]
        fila["pagos"] += 1
        if pago.tipo == TipoPago.ABONO:
            fila["abonos"] += pago.monto
            fila["recibido"] += pago.monto_recibido if pago.monto_recibido is not None else pago.monto
            fila["cambio"] += pago.cambio or cero
        else:
            fila["devoluciones"] += pago.monto
    for fila in metodos.values():
        fila["neto"] = fila["abonos"] - fila["devoluciones"]
    totales = {
        clave: sum((fila[clave] for fila in metodos.values()), cero)
        for clave in ("abonos", "devoluciones", "neto")
    }
    del_dia = list(tickets(dia))
    return {
        "dia": dia,
        "metodos": list(metodos.values()),
        "totales": totales,
        "pagos": pagos,
        "tickets": {
            "generados": len(del_dia),
            "pagados": sum(t.estado == EstadoVenta.PAGADA for t in del_dia),
            "pendientes": sum(t.estado == EstadoVenta.PENDIENTE for t in del_dia),
            "cancelados": sum(t.estado == EstadoVenta.CANCELADA for t in del_dia),
            "vendido": sum((t.total for t in del_dia if t.estado != EstadoVenta.CANCELADA), cero),
        },
    }


def tickets_con_saldo():
    """S4-14 · Tickets pendientes de cualquier día: lo que falta por cobrar (aviso en el Inicio)."""
    return (
        Venta.objects.filter(estado=EstadoVenta.PENDIENTE, saldo__gt=0)
        .select_related("cliente", "empleado", "cita__mascota")
        .order_by("fecha_hora")
    )
