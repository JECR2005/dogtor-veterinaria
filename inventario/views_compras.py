"""Pantallas de la opción Compras de la Tabla 4.8 (componente «Inventario y compras»).
Solo el Administrador (●).

UI-09 Proveedores (S2-04): búsqueda, alta, edición y baja (proveedor inactivo) con RFC válido (RF-12).
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from catalogos.models import Proveedor
from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import ProveedorForm

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
