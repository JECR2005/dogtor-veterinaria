"""Pantallas del componente «Ventas y caja» (apartado 4.2): opción Ventas y caja de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).
Ventas y caja: Recepcionista ● y Administrador ● (la Recepcionista no cancela tickets con pagos, bloque D).

UI-17 Ticket y cobro (S4-04 a S4-07): lista de tickets, nuevo ticket (también desde una cita) y detalle.
S4-08 a S4-10: pagos parciales con cambio, «Requiere factura» y PDF del ticket en tamaño carta.
UI-18 Cancelación (S4-11, S4-12): con motivo; con pagos, solo el Administrador (devolución y bitácora).
UI-19 Corte de caja (S4-13, S4-14): pagos y devoluciones del día por método, con su PDF tamaño carta.
"""

import json
from datetime import date

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from agenda.models import Cita, EstadoCita
from catalogos.models import Cliente
from catalogos.services import buscar_clientes
from catalogos.templatetags.formato import pesos
from reportes.services import pdf_desde_plantilla
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import LineasFormSet, PagoForm, iniciales_de
from .models import EstadoVenta, MetodoPago, Venta

CLIENTES_POR_PAGINA = 15


def _dia(request):
    try:
        return date.fromisoformat(request.GET.get("fecha", ""))
    except ValueError:
        return timezone.localdate()


@requiere_permiso("ventas")
def lista(request):
    """UI-17 · Tickets del día por estado y, hoy, las citas completadas que faltan por cobrar."""
    dia = _dia(request)
    estado = request.GET.get("estado", "")
    if estado not in EstadoVenta.values:
        estado = ""
    con_saldo = request.GET.get("pendientes") == "1"  # S4-14: todos los pendientes, de cualquier día
    tickets = list(services.tickets_con_saldo() if con_saldo else services.tickets(dia, estado))
    hoy = timezone.localdate()
    contexto = {
        "con_saldo": con_saldo,
        "saldo_pendiente": sum(t.saldo for t in tickets) if con_saldo else None,
        "dia": dia,
        "hoy": hoy,
        "estado": estado,
        "estados": EstadoVenta.values,
        "tickets": tickets,
        "total_del_dia": sum(t.total for t in tickets if t.estado != EstadoVenta.CANCELADA),
        "por_cobrar": list(services.citas_por_cobrar(hoy)) if dia == hoy else [],
    }
    return render(request, "ventas/lista.html", contexto)


@requiere_permiso("ventas", NIVEL_COMPLETO)
def nueva(request):
    """UI-17 · Nuevo ticket: primero el cliente (o la cita por cobrar) y después las líneas."""
    cita = None
    if request.GET.get("cita", "").isdigit():
        cita = get_object_or_404(
            Cita.objects.select_related("mascota__cliente", "servicio", "empleado"),
            pk=request.GET["cita"],
            estado=EstadoCita.COMPLETADA,
        )
        anterior = services.venta_de_la_cita(cita)
        if anterior:
            messages.info(request, f"Esa cita ya se cobró en el ticket {anterior.folio_ticket}.")
            return redirect("ventas:ticket", anterior.pk)
        cliente = cita.mascota.cliente
    elif request.GET.get("cliente", "").isdigit():
        cliente = get_object_or_404(Cliente, pk=request.GET["cliente"], activo=True)
    else:
        return _elegir_cliente(request)

    iniciales = iniciales_de(services.partidas_de_la_cita(cita)) if cita else None
    lineas = LineasFormSet(request.POST or None, prefix="lineas", initial=None if request.POST else iniciales)
    error = ""
    if request.method == "POST" and lineas.is_valid():
        try:
            venta = services.generar_ticket(cliente, request.user.empleado, lineas.partidas(), cita=cita)
        except services.ErrorVenta as rechazo:
            error = str(rechazo)
        else:
            messages.success(
                request, f"Ticket {venta.folio_ticket} generado por {pesos(venta.total)}. Registre el pago."
            )
            return redirect("ventas:ticket", venta.pk)
    contexto = {
        "cliente": cliente,
        "cita": cita,
        "lineas": lineas,
        "error": error,
        "precios": json.dumps({clave: str(precio) for clave, precio in lineas.precios.items()}),
    }
    return render(request, "ventas/nueva.html", contexto)


def _elegir_cliente(request):
    """Primer paso del ticket: la lista de clientes a la vista, filtrada por el buscador (RI-06)."""
    texto = request.GET.get("q", "").strip()
    pagina = Paginator(buscar_clientes(texto).order_by("nombre", "apellido_paterno"), CLIENTES_POR_PAGINA)
    contexto = {
        "texto": texto,
        "pagina": pagina.get_page(request.GET.get("pagina")),
        "por_cobrar": services.citas_por_cobrar(),
    }
    return render(request, "ventas/elegir_cliente.html", contexto)


def _venta(id_venta):
    return get_object_or_404(
        Venta.objects.select_related("cliente", "empleado", "cita__mascota", "cancelo"), pk=id_venta
    )


def _contexto_ticket(venta):
    return {
        "venta": venta,
        "lineas": venta.detalles.select_related("producto", "servicio", "receta").order_by("numero_linea"),
        "pagos": venta.pagos.select_related("empleado").order_by("fecha_hora", "id_pago"),
    }


@requiere_permiso("ventas")
def ticket(request, id_venta):
    """UI-17 · Detalle del ticket: líneas con su precio, total, saldo, pagos y el cobro."""
    return _pantalla_ticket(request, _venta(id_venta))


def _pantalla_ticket(request, venta, pago_form=None):
    contexto = {
        **_contexto_ticket(venta),
        "nuevo": reverse("ventas:nueva"),
        "pago_form": pago_form or PagoForm(initial={"metodo": MetodoPago.EFECTIVO, "recibido": venta.saldo}),
        "faltan_fiscales": services.datos_fiscales_faltantes(venta.cliente),
        "puede_cancelar": services.puede_cancelar(request.user, venta),
        "abonado": services.abonado(venta),
    }
    return render(request, "ventas/ticket.html", contexto)


@requiere_permiso("ventas", NIVEL_COMPLETO)
@require_POST
def pagar(request, id_venta):
    """S4-08 · Registra un abono; en efectivo calcula el cambio (RD-06)."""
    venta = _venta(id_venta)
    formulario = PagoForm(request.POST)
    if formulario.is_valid():
        datos = formulario.cleaned_data
        try:
            pago = services.registrar_pago(
                venta, request.user.empleado, datos["metodo"], datos["recibido"], datos["referencia"]
            )
        except services.ErrorVenta as error:
            formulario.add_error(None, str(error))
        else:
            venta.refresh_from_db()
            texto = f"Pago de {pesos(pago.monto)} en {pago.metodo.lower()} registrado."
            if pago.cambio:
                texto += f" Entregue {pesos(pago.cambio)} de cambio."
            texto += (
                " Ticket pagado." if venta.estado == EstadoVenta.PAGADA else f" Saldo: {pesos(venta.saldo)}."
            )
            messages.success(request, texto)
            return redirect("ventas:ticket", venta.pk)
    return _pantalla_ticket(request, venta, pago_form=formulario)


@requiere_permiso("ventas", NIVEL_COMPLETO)
@require_POST
def factura(request, id_venta):
    """S4-09 · Marca o desmarca «Requiere factura» (la factura se emite fuera del sistema)."""
    venta = _venta(id_venta)
    requiere = request.POST.get("requiere") == "si"
    try:
        services.marcar_factura(venta, requiere)
    except services.ErrorVenta as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f"Ticket {venta.folio_ticket}: requiere factura con los datos fiscales de {venta.cliente}."
            if requiere
            else f"Ticket {venta.folio_ticket}: ya no requiere factura.",
        )
    return redirect("ventas:ticket", venta.pk)


@requiere_permiso("ventas")
def ticket_pdf(request, id_venta):
    """S4-10 · PDF del ticket en tamaño carta (RF-13, D-18)."""
    venta = _venta(id_venta)
    respuesta = HttpResponse(
        pdf_desde_plantilla("reportes/ticket.html", _contexto_ticket(venta)), content_type="application/pdf"
    )
    respuesta["Content-Disposition"] = f'inline; filename="Ticket-{venta.folio_ticket}.pdf"'
    return respuesta


@requiere_permiso("ventas", NIVEL_COMPLETO)
def cancelar(request, id_venta):
    """UI-18 · Cancelación con motivo y resumen de lo que se devuelve y lo que regresa al inventario."""
    venta = _venta(id_venta)
    if venta.estado == EstadoVenta.CANCELADA:
        messages.info(request, f"El ticket {venta.folio_ticket} ya está cancelado.")
        return redirect("ventas:ticket", venta.pk)
    if not services.puede_cancelar(request.user, venta):
        raise PermissionDenied("Solo el Administrador cancela un ticket con pagos (RF-14).")
    error = ""
    motivo = request.POST.get("motivo", "")
    if request.method == "POST":
        try:
            services.cancelar_venta(venta, request.user, motivo)
        except services.ErrorVenta as rechazo:
            error = str(rechazo)
        else:
            messages.success(
                request, f"Ticket {venta.folio_ticket} cancelado. Quedó registrado en la bitácora."
            )
            return redirect("ventas:ticket", venta.pk)
    contexto = {
        "venta": venta,
        "resumen": services.resumen_cancelacion(venta),
        "motivo": motivo,
        "error": error,
        "maximo": services.MOTIVO_MAXIMO,
    }
    return render(request, "ventas/cancelar.html", contexto)


@requiere_permiso("ventas")
def corte(request):
    """UI-19 · Corte de caja del día por método de pago: abonos, devoluciones y neto (RF-13, TI-12)."""
    dia = _dia(request)
    return render(request, "ventas/corte.html", {**services.corte_de_caja(dia), "hoy": timezone.localdate()})


@requiere_permiso("ventas")
def corte_pdf(request):
    """S4-14 · PDF del corte de caja en tamaño carta, para firmarlo al cerrar el día."""
    datos = services.corte_de_caja(_dia(request))
    respuesta = HttpResponse(
        pdf_desde_plantilla("reportes/corte.html", {**datos, "imprimio": request.user.empleado}),
        content_type="application/pdf",
    )
    respuesta["Content-Disposition"] = f'inline; filename="Corte-{datos["dia"]:%Y-%m-%d}.pdf"'
    return respuesta
