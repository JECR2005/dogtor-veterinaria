"""Pantallas del componente «Inventario y compras» (apartado 4.2): opción Inventario de la Tabla 4.8.

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene). Inventario: solo el
Administrador (●).

UI-08 Productos (S2-05): lista con distintivos de stock bajo, por caducar y lote vencido (RI-02);
alta y edición.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from catalogos.models import CategoriaProducto, Producto
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import ProductoForm

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
        return redirect("inventario:productos")
    contexto = {"formulario": formulario, "producto": producto, "unidades": UNIDADES_SUGERIDAS}
    return render(request, "inventario/productos/formulario.html", contexto)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_nuevo(request):
    return _formulario(request)


@requiere_permiso("inventario", NIVEL_COMPLETO)
def producto_editar(request, id_producto):
    return _formulario(request, get_object_or_404(Producto, pk=id_producto))
