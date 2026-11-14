"""Pantallas del componente «Catálogos» (apartado 4.2).

Cada vista se declara con `@requiere_permiso("<opción de la Tabla 4.9>")` de seguridad/permisos.py
(RNF-01: escribir la dirección de una pantalla no da acceso a quien no lo tiene).

UI-05 Clientes (S1-08): búsqueda, ficha, alta con aviso de privacidad, edición y baja lógica.
UI-06 Mascotas (S1-09): alta que abre su expediente, ficha y edición.
Clientes y mascotas: Recepcionista ● completo; Administrador, Veterinario y Estilista ○ consulta.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import Rol
from seguridad.permisos import requiere_permiso

from . import services
from .forms import ClienteForm, MascotaForm
from .models import Cliente, EstatusMascota, Mascota

CLIENTES_POR_PAGINA = 25


def _puede_ver_dados_de_baja(usuario):
    """RF-01: el historial de un cliente dado de baja sigue disponible para el Administrador."""
    return usuario.rol == Rol.ADMINISTRADOR


def _cliente_visible(request, id_cliente):
    cliente = get_object_or_404(Cliente, pk=id_cliente)
    if not cliente.activo and not _puede_ver_dados_de_baja(request.user):
        raise Http404
    return cliente


@requiere_permiso("clientes")
def lista(request):
    """UI-05 · Búsqueda de clientes; también recibe la búsqueda global de la barra superior."""
    texto = request.GET.get("q", "").strip()
    ver_bajas = _puede_ver_dados_de_baja(request.user) and request.GET.get("bajas") == "1"
    clientes = services.buscar_clientes(texto, incluir_dados_de_baja=ver_bajas)
    pagina = Paginator(clientes, CLIENTES_POR_PAGINA).get_page(request.GET.get("pagina"))
    contexto = {
        "pagina": pagina,
        "texto": texto,
        "ver_bajas": ver_bajas,
        "puede_ver_bajas": _puede_ver_dados_de_baja(request.user),
    }
    return render(request, "catalogos/clientes/lista.html", contexto)


@requiere_permiso("clientes")
def ficha(request, id_cliente):
    """UI-05 · Ficha del cliente con sus mascotas (RF-01, RF-02)."""
    cliente = _cliente_visible(request, id_cliente)
    mascotas = cliente.mascotas.select_related("raza__especie").order_by("nombre")
    return render(request, "catalogos/clientes/ficha.html", {"cliente": cliente, "mascotas": mascotas})


@requiere_permiso("clientes", NIVEL_COMPLETO)
def nuevo(request):
    """UI-05 · Alta de cliente. Sin aviso de privacidad no se guarda (RF-01, RNF-08)."""
    formulario = ClienteForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        cliente = services.registrar_cliente(formulario)
        messages.success(request, f"Cliente «{cliente}» registrado.")
        return redirect("catalogos:ficha", id_cliente=cliente.pk)
    return render(request, "catalogos/clientes/formulario.html", {"formulario": formulario})


@requiere_permiso("clientes", NIVEL_COMPLETO)
def editar(request, id_cliente):
    cliente = get_object_or_404(Cliente, pk=id_cliente, activo=True)
    formulario = ClienteForm(request.POST or None, instance=cliente)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Datos del cliente actualizados.")
        return redirect("catalogos:ficha", id_cliente=cliente.pk)
    contexto = {"formulario": formulario, "cliente": cliente}
    return render(request, "catalogos/clientes/formulario.html", contexto)


@requiere_permiso("clientes", NIVEL_COMPLETO)
def confirmar_baja(request, id_cliente):
    cliente = get_object_or_404(Cliente, pk=id_cliente, activo=True)
    return render(request, "catalogos/clientes/baja.html", {"cliente": cliente})


@requiere_permiso("clientes", NIVEL_COMPLETO)
@require_POST
def baja(request, id_cliente):
    """Baja lógica con registro en la bitácora (RF-01, RNF-03, RNF-08)."""
    cliente = get_object_or_404(Cliente, pk=id_cliente)
    try:
        services.dar_de_baja_cliente(cliente, request.user)
    except services.OperacionNoValida as error:
        messages.error(request, str(error))
        return redirect("catalogos:lista")
    messages.success(request, f"Cliente «{cliente}» dado de baja. Su historial se conserva.")
    return redirect("catalogos:lista")


# --- UI-06 · Mascotas ---------------------------------------------------------
def _mascota_visible(request, id_mascota):
    mascota = get_object_or_404(Mascota.objects.select_related("cliente", "raza__especie"), pk=id_mascota)
    if not mascota.cliente.activo and not _puede_ver_dados_de_baja(request.user):
        raise Http404
    return mascota


@requiere_permiso("clientes", NIVEL_COMPLETO)
def nueva_mascota(request, id_cliente):
    """UI-06 · Alta de mascota; al guardar se abre su expediente (RF-02, RD-10)."""
    cliente = get_object_or_404(Cliente, pk=id_cliente, activo=True)
    formulario = MascotaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        mascota = services.registrar_mascota(cliente, formulario)
        messages.success(request, f"Mascota «{mascota}» registrada y su expediente abierto.")
        return redirect("catalogos:mascota", id_mascota=mascota.pk)
    contexto = {"formulario": formulario, "cliente": cliente}
    return render(request, "catalogos/mascotas/formulario.html", contexto)


@requiere_permiso("clientes")
def mascota(request, id_mascota):
    """UI-06 · Ficha de la mascota con los datos de su expediente."""
    mascota = _mascota_visible(request, id_mascota)
    expediente = getattr(mascota, "expediente", None)  # RD-10: toda mascota debería tener uno
    from agenda.services import citas_visibles  # D-17: cada rol ve solo las citas que le tocan

    citas = citas_visibles(request.user, mascota.citas.select_related("servicio", "empleado"))
    citas = citas.order_by("-fecha_hora_inicio")[:10]
    contexto = {
        "mascota": mascota,
        "expediente": expediente,
        "citas": citas,
        "puede_agendar": request.user.tiene_permiso("agenda", NIVEL_COMPLETO)
        and mascota.cliente.activo
        and mascota.estatus == EstatusMascota.ACTIVA,
    }
    return render(request, "catalogos/mascotas/ficha.html", contexto)


@requiere_permiso("clientes", NIVEL_COMPLETO)
def editar_mascota(request, id_mascota):
    mascota = get_object_or_404(
        Mascota.objects.select_related("cliente"), pk=id_mascota, cliente__activo=True
    )
    formulario = MascotaForm(request.POST or None, instance=mascota)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Datos de la mascota actualizados.")
        return redirect("catalogos:mascota", id_mascota=mascota.pk)
    contexto = {"formulario": formulario, "cliente": mascota.cliente, "mascota": mascota}
    return render(request, "catalogos/mascotas/formulario.html", contexto)
