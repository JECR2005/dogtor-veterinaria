"""UI-04 · Catálogo de servicios (S1-11, RF-04, RD-04). Solo el Administrador (Administración ●)."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from .forms import ServicioForm
from .models import CategoriaServicio, Servicio


@requiere_permiso("administracion", NIVEL_COMPLETO)
def lista(request):
    """UI-04 · Servicios con filtro por categoría; los inactivos solo si se piden."""
    categoria = request.GET.get("categoria", "")
    ver_inactivos = request.GET.get("inactivos") == "1"
    servicios = Servicio.objects.order_by("categoria", "nombre")
    if categoria in CategoriaServicio.values:
        servicios = servicios.filter(categoria=categoria)
    else:
        categoria = ""
    if not ver_inactivos:
        servicios = servicios.filter(activo=True)
    contexto = {
        "servicios": servicios,
        "categorias": CategoriaServicio.choices,
        "categoria": categoria,
        "ver_inactivos": ver_inactivos,
    }
    return render(request, "catalogos/servicios/lista.html", contexto)


def _formulario(request, servicio=None):
    formulario = ServicioForm(request.POST or None, instance=servicio)
    if request.method == "POST" and formulario.is_valid():
        guardado = formulario.save()
        accion = "actualizado" if servicio else "registrado"
        messages.success(request, f"Servicio «{guardado}» {accion}.")
        return redirect("servicios:lista")
    return render(
        request, "catalogos/servicios/formulario.html", {"formulario": formulario, "servicio": servicio}
    )


@requiere_permiso("administracion", NIVEL_COMPLETO)
def nuevo(request):
    return _formulario(request)


@requiere_permiso("administracion", NIVEL_COMPLETO)
def editar(request, id_servicio):
    return _formulario(request, get_object_or_404(Servicio, pk=id_servicio))
