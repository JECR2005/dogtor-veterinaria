"""Pantallas del componente «Ventas y caja» (apartado 4.2): opción Ventas y caja de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).
Ventas y caja: Recepcionista ● y Administrador ● (la Recepcionista no cancela tickets con pagos, bloque D).

UI-17 Ticket y cobro (S4-04 a S4-07): lista de tickets, nuevo ticket (también desde una cita) y detalle.
"""

import json
from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import Cliente
from catalogos.services import buscar_clientes
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import LineasFormSet, iniciales_de
from .models import EstadoVenta, Venta

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
    tickets = list(services.tickets(dia, estado))
    hoy = timezone.localdate()
    contexto = {
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
            from catalogos.templatetags.formato import pesos

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


@requiere_permiso("ventas")
def ticket(request, id_venta):
    """UI-17 · Detalle del ticket: líneas con su precio, total, saldo y pagos."""
    venta = get_object_or_404(
        Venta.objects.select_related("cliente", "empleado", "cita__mascota", "cancelo"), pk=id_venta
    )
    contexto = {
        "venta": venta,
        "lineas": venta.detalles.select_related("producto", "servicio", "receta").order_by("numero_linea"),
        "pagos": venta.pagos.select_related("empleado").order_by("fecha_hora", "id_pago"),
        "nuevo": reverse("ventas:nueva"),
    }
    return render(request, "ventas/ticket.html", contexto)
