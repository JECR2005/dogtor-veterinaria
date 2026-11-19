"""Pantallas del componente «Inventario y compras» (apartado 4.2): opción Inventario de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene). Inventario: solo el
Administrador (●).

UI-08 Productos (S2-05): lista con distintivos de stock bajo, por caducar y lote vencido (RI-02);
alta y edición.
UI-08 Lotes y movimientos (S2-08): ficha del producto con sus lotes y su kardex; entradas y ajustes con
motivo, que se confirman antes de aplicarse (RI-04). Alertas (S2-09).
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalogos.models import CategoriaProducto, Producto
from catalogos.templatetags.formato import cantidad
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import AjusteForm, EntradaForm, ProductoForm
from .models import Lote, MovimientoInventario

PRODUCTOS_POR_PAGINA = 25
UNIDADES_SUGERIDAS = ["Pieza", "Dosis", "Tableta", "mL", "Frasco", "Bolsa", "Botella", "kg"]


@requiere_permiso("inventario")
def productos(request):
    """UI-08 · Productos con sus existencias vigentes y distintivos; filtros por texto, categoría y alerta."""
    texto = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    if categoria not in CategoriaProducto.values:
        categoria = ""
    alerta = request.GET.get("alerta", "")
    if alerta not in services.FILTROS_ALERTA:
        alerta = ""
    ver_inactivos = request.GET.get("inactivos") == "1"
    encontrados = services.buscar_productos(texto, categoria, alerta, ver_inactivos)
    pagina = Paginator(encontrados, PRODUCTOS_POR_PAGINA).get_page(request.GET.get("pagina"))
    for producto in pagina.object_list:
        producto.distintivos = services.distintivos(producto)
    contexto = {
        "pagina": pagina,
        "texto": texto,
        "categoria": categoria,
        "categorias": CategoriaProducto.choices,
        "alerta": alerta,
        "alertas": services.FILTROS_ALERTA.items(),
        "ver_inactivos": ver_inactivos,
        "filtrado": bool(texto or categoria or alerta or ver_inactivos),
    }
    return render(request, "inventario/productos/lista.html", contexto)


def _formulario(request, producto=None):
    formulario = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and formulario.is_valid():
        guardado = formulario.save()
        accion = "actualizado" if producto else "registrado"
        messages.success(request, f"Producto «{guardado.nombre}» {accion}.")
        return redirect("inventario:producto", guardado.pk)
    contexto = {"formulario": formulario, "producto": producto, "unidades": UNIDADES_SUGERIDAS}
    return render(request, "inventario/productos/formulario.html", contexto)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_nuevo(request):
    return _formulario(request)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_editar(request, id_producto):
    return _formulario(request, get_object_or_404(Producto, pk=id_producto))


MOVIMIENTOS_EN_FICHA = 50


@requiere_permiso("inventario")
def producto(request, id_producto):
    """UI-08 · Ficha del producto: existencias, lotes del que caduca primero al último y kardex."""
    producto = get_object_or_404(services.productos_con_existencias(), pk=id_producto)
    producto.distintivos = services.distintivos(producto)
    lotes = list(
        Lote.objects.filter(producto=producto).order_by(
            F("fecha_caducidad").asc(nulls_last=True), "fecha_entrada", "id_lote"
        )
    )
    for lote in lotes:
        lote.estado_texto = lote.estado()
    movimientos = (
        MovimientoInventario.objects.filter(lote__producto=producto)
        .select_related("lote", "empleado")
        .order_by("-fecha_hora", "-id_movimiento")
    )
    contexto = {
        "producto": producto,
        "lotes": lotes,
        "movimientos": movimientos[:MOVIMIENTOS_EN_FICHA],
        "total_movimientos": movimientos.count(),
    }
    return render(request, "inventario/productos/ficha.html", contexto)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_entrada(request, id_producto):
    """Entrada de mercancía sin pedido: crea el lote o suma al mismo número y caducidad."""
    producto = get_object_or_404(Producto, pk=id_producto)
    formulario = EntradaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        datos = formulario.cleaned_data
        try:
            lote = services.registrar_entrada(
                producto,
                datos["numero_lote"],
                datos["cantidad"],
                request.user.empleado,
                fecha_caducidad=datos["fecha_caducidad"],
                referencia=datos["referencia"],
            )
        except services.ErrorInventario as error:
            formulario.add_error("numero_lote", str(error))
        else:
            messages.success(
                request,
                f"Entrada registrada: {cantidad(datos['cantidad'])} {producto.unidad_medida} al lote "
                f"{lote.numero_lote}. Ahora tiene {cantidad(lote.cantidad_disponible)}.",
            )
            return redirect("inventario:producto", producto.pk)
    return render(
        request, "inventario/productos/entrada.html", {"producto": producto, "formulario": formulario}
    )


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_ajuste(request, id_producto):
    """Ajuste con motivo (R08). Primero muestra el resumen y solo se aplica al confirmar (RI-04)."""
    producto = get_object_or_404(Producto, pk=id_producto)
    inicial = {}
    if request.method == "GET" and request.GET.get("lote"):
        lote = Lote.objects.filter(producto=producto, pk=request.GET["lote"]).first()
        if lote and lote.esta_vencido() and lote.cantidad_disponible > 0:
            # Desechar un lote vencido: se quita todo lo que queda
            inicial = {
                "lote": lote,
                "sentido": "disminuir",
                "cantidad": lote.cantidad_disponible,
                "motivo": "Lote vencido desechado",
            }
        elif lote:
            inicial = {"lote": lote}
    formulario = AjusteForm(producto, request.POST or None, initial=inicial)
    if request.method == "POST" and formulario.is_valid():
        lote = formulario.cleaned_data["lote"]
        cambio = formulario.cantidad_con_signo()
        resultado = lote.cantidad_disponible + cambio
        if resultado < 0:
            formulario.add_error(
                "cantidad",
                f"El lote {lote.numero_lote} tiene {cantidad(lote.cantidad_disponible)}; "
                "no se puede quitar más.",
            )
        elif request.POST.get("confirmar") == "1":
            try:
                lote = services.ajustar(
                    lote, cambio, formulario.cleaned_data["motivo"], request.user.empleado
                )
            except services.ErrorInventario as error:
                formulario.add_error(None, str(error))
            else:
                messages.success(
                    request,
                    f"Ajuste registrado en el lote {lote.numero_lote}: "
                    f"ahora tiene {cantidad(lote.cantidad_disponible)}.",
                )
                return redirect("inventario:producto", producto.pk)
        else:
            contexto = {
                "producto": producto,
                "formulario": formulario,
                "lote": lote,
                "cambio": cambio,
                "resultado": resultado,
            }
            return render(request, "inventario/productos/ajuste_confirmar.html", contexto)
    return render(
        request, "inventario/productos/ajuste.html", {"producto": producto, "formulario": formulario}
    )


@requiere_permiso("inventario")
def alertas(request):
    """S2-09 · Alertas de RF-11: stock bajo, lotes por caducar en 30 días y lotes vencidos con piezas."""
    hoy = timezone.localdate()
    avisos = services.alertas(hoy)
    for lote in avisos["por_caducar"]:
        dias = (lote.fecha_caducidad - hoy).days
        lote.cuando = "hoy" if dias == 0 else f"en {dias} día{'s' if dias != 1 else ''}"
    return render(request, "inventario/alertas.html", {**avisos, "dias": services.DIAS_AVISO_CADUCIDAD})
