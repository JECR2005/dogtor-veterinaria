"""UI-20 · Bitácora y exportación (S5-05, S5-06): solo el Administrador (Tabla 4.9, RNF-03, RNF-08).

- Consulta por fecha, usuario, acción y qué se modificó, con los valores previos de cada registro.
- Exportación a CSV de lo filtrado; la exportación misma queda en la bitácora.
- Exportación de los contactos de los clientes activos, registrada en la bitácora (RNF-08): los dados de baja
  no salen. Las exportaciones se piden con POST porque dejan registro.
"""

import csv
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone

from catalogos.models import Cliente

from . import bitacora
from .menu import NIVEL_COMPLETO
from .models import AccionBitacora, Usuario
from .permisos import requiere_permiso

POR_PAGINA = 50
DIAS_POR_DEFECTO = 7


class FiltroBitacoraForm(forms.Form):
    desde = forms.DateField(label="Desde", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    hasta = forms.DateField(label="Hasta", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    usuario = forms.ModelChoiceField(
        label="Usuario",
        queryset=Usuario.objects.select_related("empleado").order_by("nombre_usuario"),
        required=False,
        empty_label="Todos",
    )
    accion = forms.ChoiceField(label="Acción", required=False)
    entidad = forms.ChoiceField(label="Qué", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accion"].choices = [("", "Todas"), *AccionBitacora.choices]
        self.fields["entidad"].choices = [
            ("", "Todo"),
            *sorted(bitacora.ENTIDADES.items(), key=lambda e: e[1]),
        ]
        self.fields["usuario"].label_from_instance = lambda u: f"{u.nombre_usuario} ({u.empleado.nombre})"
        for campo in self.fields.values():
            clase = "form-select" if isinstance(campo, forms.ChoiceField) else "form-control"
            campo.widget.attrs.setdefault("class", clase)

    def clean(self):
        datos = super().clean()
        if datos.get("desde") and datos.get("hasta") and datos["desde"] > datos["hasta"]:
            raise forms.ValidationError("La fecha «Desde» es posterior a «Hasta».")
        return datos


def _filtro(datos):
    hoy = timezone.localdate()
    iniciales = {"desde": hoy - timedelta(days=DIAS_POR_DEFECTO - 1), "hasta": hoy}
    formulario = FiltroBitacoraForm({**{k: v.isoformat() for k, v in iniciales.items()}, **datos.dict()})
    if formulario.is_valid():
        return formulario, formulario.cleaned_data
    return formulario, {**iniciales, "usuario": None, "accion": "", "entidad": ""}


def _registros(filtros):
    return bitacora.buscar(
        filtros["desde"], filtros["hasta"], filtros["usuario"], filtros["accion"], filtros["entidad"]
    )


def _descripcion_filtros(filtros):
    return {
        "desde": filtros["desde"].isoformat(),
        "hasta": filtros["hasta"].isoformat(),
        "usuario": filtros["usuario"].nombre_usuario if filtros["usuario"] else None,
        "accion": filtros["accion"] or None,
        "entidad": filtros["entidad"] or None,
    }


def _csv(nombre, columnas, filas):
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    respuesta.write("﻿")  # BOM: Excel abre los acentos correctamente
    escritor = csv.writer(respuesta)
    escritor.writerow(columnas)
    escritor.writerows(filas)
    return respuesta


@requiere_permiso("bitacora", NIVEL_COMPLETO)
def lista(request):
    """UI-20 · Consulta de la bitácora con filtros y valores previos."""
    formulario, filtros = _filtro(request.GET)
    pagina = Paginator(_registros(filtros), POR_PAGINA).get_page(request.GET.get("pagina"))
    filas = [
        {
            "registro": registro,
            "que": bitacora.nombre_de_entidad(registro.entidad),
            "previos": bitacora.valores_previos(registro),
        }
        for registro in pagina.object_list
    ]
    consulta = request.GET.copy()
    consulta.pop("pagina", None)
    contexto = {
        "formulario": formulario,
        "filtros": filtros,
        "pagina": pagina,
        "filas": filas,
        "consulta": consulta.urlencode(),
        "contactos": Cliente.objects.filter(activo=True).count(),
    }
    return render(request, "bitacora/lista.html", contexto)


@requiere_permiso("bitacora", NIVEL_COMPLETO)
def exportar(request):
    """Exporta a CSV lo filtrado; la exportación queda registrada en la bitácora (UI-20, RNF-03)."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    _, filtros = _filtro(request.POST)
    with transaction.atomic():
        registros = list(_registros(filtros))
        bitacora.registrar_exportacion(
            request.user,
            "bitacora_auditoria",
            {"filtros": _descripcion_filtros(filtros), "registros": len(registros)},
        )
    nombre = f"bitacora_{filtros['desde']:%Y%m%d}_{filtros['hasta']:%Y%m%d}.csv"
    return _csv(nombre, bitacora.COLUMNAS_CSV, (bitacora.fila_csv(r) for r in registros))


COLUMNAS_CONTACTOS = ["Nombre", "Apellido paterno", "Apellido materno", "Teléfono", "Correo", "Prefiere"]


@requiere_permiso("bitacora", NIVEL_COMPLETO)
def contactos(request):
    """S5-06 · Exporta los contactos de los clientes activos que aceptaron el aviso (RNF-08), con registro."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.POST.get("acepto") != "1":
        messages.error(request, "Confirme que los contactos se usarán solo para las finalidades del aviso.")
        return redirect("bitacora:lista")
    with transaction.atomic():
        clientes = list(
            Cliente.objects.filter(activo=True, acepto_aviso_privacidad=True).order_by(
                "apellido_paterno", "apellido_materno", "nombre"
            )
        )
        bitacora.registrar_exportacion(
            request.user, "contactos", {"registros": len(clientes), "campos": COLUMNAS_CONTACTOS}
        )
    filas = (
        [
            c.nombre,
            c.apellido_paterno,
            c.apellido_materno or "",
            c.telefono,
            c.correo or "",
            c.preferencia_contacto,
        ]
        for c in clientes
    )
    return _csv(f"contactos_{timezone.localdate():%Y%m%d}.csv", COLUMNAS_CONTACTOS, filas)
