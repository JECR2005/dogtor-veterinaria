"""Pantallas de la opción Compras de la Tabla 4.8 (componente «Inventario y compras»).
Solo el Administrador (●).

UI-09 Proveedores (S2-04): búsqueda, alta, edición y baja (proveedor inactivo) con RFC válido (RF-12).
UI-09 Pedidos (S2-10): partidas con total, edición y cancelación mientras está Pendiente.
UI-10 Recepción (S2-11): al recibir, cada partida crea su lote con caducidad y su entrada (TI-03).
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from catalogos.models import Producto, Proveedor
from catalogos.templatetags.formato import pesos
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import PartidasFormSet, PedidoForm, ProveedorForm, RecepcionPartidaForm
from .models import EstadoPedido, MovimientoInventario, PedidoCompra, TipoMovimiento

PROVEEDORES_POR_PAGINA = 25


@requiere_permiso("compras")
def proveedores(request):
    """UI-09 · Proveedores por razón social, RFC o contacto; los inactivos solo si se piden."""
    texto = request.GET.get("q", "").strip()
    ver_inactivos = request.GET.get("inactivos") == "1"
    encontrados = services.buscar_proveedores(texto, ver_inactivos)
    pagina = Paginator(encontrados, PROVEEDORES_POR_PAGINA).get_page(request.GET.get("pagina"))
    contexto = {"pagina": pagina, "texto": texto, "ver_inactivos": ver_inactivos}
    return render(request, "inventario/proveedores/lista.html", contexto)


def _formulario(request, proveedor=None):
    formulario = ProveedorForm(request.POST or None, instance=proveedor)
    if request.method == "POST" and formulario.is_valid():
        guardado = formulario.save()
        if proveedor and not guardado.activo:
            messages.success(
                request, f"Proveedor «{guardado}» dado de baja; sus pedidos anteriores se conservan."
            )
        else:
            accion = "actualizado" if proveedor else "registrado"
            messages.success(request, f"Proveedor «{guardado}» {accion}.")
        return redirect("compras:proveedores")
    return render(
        request, "inventario/proveedores/formulario.html", {"formulario": formulario, "proveedor": proveedor}
    )


@requiere_permiso("compras", NIVEL_COMPLETO)
def proveedor_nuevo(request):
    return _formulario(request)


@requiere_permiso("compras", NIVEL_COMPLETO)
def proveedor_editar(request, id_proveedor):
    return _formulario(request, get_object_or_404(Proveedor, pk=id_proveedor))


# --- S2-10 · Pedidos de compra (UI-09) ------------------------------------------------
PEDIDOS_POR_PAGINA = 25


@requiere_permiso("compras")
def pedidos(request):
    """UI-09 · Pedidos del más reciente al más antiguo, con filtro por estado y proveedor."""
    estado = request.GET.get("estado", "")
    if estado not in EstadoPedido.values:
        estado = ""
    proveedor = request.GET.get("proveedor", "")
    lista = PedidoCompra.objects.select_related("proveedor").annotate(partidas=Count("detalles"))
    if estado:
        lista = lista.filter(estado=estado)
    if proveedor.isdigit():
        lista = lista.filter(proveedor_id=int(proveedor))
    else:
        proveedor = ""
    pagina = Paginator(lista.order_by("-fecha_pedido", "-id_pedido"), PEDIDOS_POR_PAGINA).get_page(
        request.GET.get("pagina")
    )
    contexto = {
        "pagina": pagina,
        "estado": estado,
        "estados": EstadoPedido.choices,
        "proveedor": proveedor,
        "proveedores": Proveedor.objects.order_by("razon_social"),
        "pestana": "recibir" if estado == EstadoPedido.PENDIENTE else "pedidos",
    }
    return render(request, "inventario/pedidos/lista.html", contexto)


def _formulario_pedido(request, pedido=None):
    if pedido is not None and pedido.estado != EstadoPedido.PENDIENTE:
        messages.error(
            request, f"El pedido {pedido.folio} ya está {pedido.estado.lower()}; no se puede cambiar."
        )
        return redirect("compras:pedido", pedido.pk)
    if request.method == "POST":
        formulario = PedidoForm(request.POST)
        partidas = PartidasFormSet(request.POST, prefix="partidas")
        if formulario.is_valid() and partidas.is_valid():
            try:
                guardado = services.guardar_pedido(
                    formulario.cleaned_data["proveedor"], request.user.empleado, partidas.partidas(), pedido
                )
            except services.ErrorInventario as error:
                formulario.add_error(None, str(error))
            else:
                accion = "actualizado" if pedido else "registrado"
                messages.success(request, f"Pedido {guardado.folio} {accion} por {pesos(guardado.total)}.")
                return redirect("compras:pedido", guardado.pk)
    elif pedido is not None:
        formulario = PedidoForm(initial={"proveedor": pedido.proveedor})
        iniciales = [
            {"producto": d.producto, "cantidad": d.cantidad_solicitada, "costo_unitario": d.costo_unitario}
            for d in pedido.detalles.select_related("producto").order_by("id_detalle_pedido")
        ]
        partidas = PartidasFormSet(initial=iniciales, prefix="partidas")
    else:
        # Desde una alerta de stock bajo: «Pedir» llega con el producto y su proveedor habitual
        producto = Producto.objects.filter(pk=request.GET.get("producto") or 0, activo=True).first()
        iniciales = [{"producto": producto}] if producto else []
        proveedor = (
            producto.proveedor if producto and producto.proveedor and producto.proveedor.activo else None
        )
        formulario = PedidoForm(initial={"proveedor": proveedor})
        partidas = PartidasFormSet(initial=iniciales, prefix="partidas")
    contexto = {"formulario": formulario, "partidas": partidas, "pedido": pedido}
    return render(request, "inventario/pedidos/formulario.html", contexto)


@requiere_permiso("compras", NIVEL_COMPLETO)
def pedido_nuevo(request):
    return _formulario_pedido(request)


@requiere_permiso("compras", NIVEL_COMPLETO)
def pedido_editar(request, id_pedido):
    return _formulario_pedido(request, get_object_or_404(PedidoCompra, pk=id_pedido))


@requiere_permiso("compras")
def pedido(request, id_pedido):
    """UI-09 · Detalle del pedido con sus partidas; si ya se recibió, lo que llegó de cada una."""
    pedido = get_object_or_404(PedidoCompra.objects.select_related("proveedor", "empleado"), pk=id_pedido)
    detalles = list(pedido.detalles.select_related("producto").order_by("id_detalle_pedido"))
    for detalle in detalles:
        detalle.importe = detalle.cantidad_solicitada * detalle.costo_unitario
    lotes = []
    if pedido.estado == EstadoPedido.RECIBIDO:
        lotes = (
            MovimientoInventario.objects.filter(referencia=pedido.folio, tipo=TipoMovimiento.ENTRADA)
            .select_related("lote", "lote__producto")
            .order_by("id_movimiento")
        )
    return render(
        request, "inventario/pedidos/ficha.html", {"pedido": pedido, "detalles": detalles, "entradas": lotes}
    )


@requiere_permiso("compras", NIVEL_COMPLETO)
def pedido_cancelar(request, id_pedido):
    """Cancelar un pedido Pendiente, con confirmación (RI-04)."""
    pedido = get_object_or_404(PedidoCompra.objects.select_related("proveedor"), pk=id_pedido)
    if request.method == "POST":
        try:
            services.cancelar_pedido(pedido, request.user.empleado)
        except services.ErrorInventario as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Pedido {pedido.folio} cancelado.")
        return redirect("compras:pedido", pedido.pk)
    if pedido.estado != EstadoPedido.PENDIENTE:
        messages.error(
            request, f"El pedido {pedido.folio} ya está {pedido.estado.lower()}; no se puede cancelar."
        )
        return redirect("compras:pedido", pedido.pk)
    return render(request, "inventario/pedidos/cancelar.html", {"pedido": pedido})


# --- S2-11 · Recepción del pedido (UI-10) ------------------------------------------------
@requiere_permiso("compras", NIVEL_COMPLETO)
def pedido_recibir(request, id_pedido):
    """UI-10 · Por partida: cantidad recibida, número de lote y caducidad. Al guardar se crean los lotes."""
    pedido = get_object_or_404(PedidoCompra.objects.select_related("proveedor"), pk=id_pedido)
    if pedido.estado != EstadoPedido.PENDIENTE:
        messages.error(
            request, f"El pedido {pedido.folio} ya está {pedido.estado.lower()}; no se puede recibir."
        )
        return redirect("compras:pedido", pedido.pk)
    detalles = list(pedido.detalles.select_related("producto").order_by("id_detalle_pedido"))
    formularios = [RecepcionPartidaForm(d, request.POST or None) for d in detalles]
    error = None
    if request.method == "POST" and all([f.is_valid() for f in formularios]):
        recepcion = {
            f.detalle.pk: (
                f.cleaned_data["cantidad_recibida"],
                f.cleaned_data["numero_lote"],
                f.cleaned_data["fecha_caducidad"],
            )
            for f in formularios
        }
        try:
            lotes = services.recibir_pedido(pedido, request.user.empleado, recepcion)
        except services.ErrorInventario as problema:
            error = str(problema)
        else:
            messages.success(
                request,
                f"Pedido {pedido.folio} recibido: {len(lotes)} lote{'s' if len(lotes) != 1 else ''} "
                "con su entrada; las existencias ya están actualizadas.",
            )
            return redirect("compras:pedido", pedido.pk)
    contexto = {"pedido": pedido, "formularios": formularios, "error": error}
    return render(request, "inventario/pedidos/recibir.html", contexto)
