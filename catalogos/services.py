"""Servicios (reglas de negocio) del componente «Catálogos».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P1 y P2:

- RF-01: alta, edición y baja lógica de clientes con aviso de privacidad (P1).
- RF-02 y RD-10: alta de mascota que abre su único expediente clínico (P1).
- RF-03 y RD-01: empleados con horario; cédula obligatoria para el veterinario (P1).
- RF-04: catálogo de servicios con precio y duración (P1).
"""

from functools import reduce
from operator import and_

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import CharField, Count, Func, Q

from seguridad import bitacora
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import AccionBitacora

from .forms import solo_digitos
from .models import Cliente


class OperacionNoValida(Exception):
    """Regla de negocio incumplida; el mensaje se muestra tal cual al usuario (RI-08)."""


def dar_de_baja_cliente(cliente, usuario):
    """Baja lógica de un cliente (RF-01, RNF-08) con su registro en la bitácora (RNF-03, S1-07).

    El cliente no se borra: queda con activo = 0 y deja de aparecer en búsquedas; su historial y sus
    tickets se conservan. Solo un rol con Clientes en nivel completo (Recepcionista) puede hacerlo.
    """
    if not usuario.tiene_permiso("clientes", NIVEL_COMPLETO):
        raise PermissionDenied
    with transaction.atomic():
        actual = Cliente.objects.select_for_update().get(pk=cliente.pk)
        if not actual.activo:
            raise OperacionNoValida("El cliente ya está dado de baja.")
        previos = bitacora.valores_de(actual)
        Cliente.objects.filter(pk=actual.pk).update(activo=False)
        bitacora.registrar(usuario, AccionBitacora.BAJA_LOGICA, actual, previos)
    cliente.activo = False
    return cliente


class SinAcentos(Func):
    """Compara sin acentos ni mayúsculas. Collate() de Django pone la intercalación entre corchetes,
    que SQL Server no acepta en COLLATE; por eso se escribe fija aquí."""

    template = "%(expressions)s COLLATE Modern_Spanish_CI_AI"
    output_field = CharField()


def buscar_clientes(texto="", incluir_dados_de_baja=False):
    """Búsqueda de UI-05 y de la barra superior: por nombre, apellidos, teléfono o nombre de mascota.

    Cada palabra escrita debe aparecer en alguno de esos datos («ana 833» encuentra a Ana con teléfono
    que contiene 833). Los clientes dados de baja no aparecen (RF-01), salvo que el Administrador pida
    verlos para consultar su historial.
    """
    clientes = Cliente.objects.all()
    if not incluir_dados_de_baja:
        clientes = clientes.filter(activo=True)
    condiciones = []
    for palabra in (texto or "").split():
        condicion = (
            Q(_nombre__icontains=palabra)
            | Q(_paterno__icontains=palabra)
            | Q(_materno__icontains=palabra)
            | Q(_mascota__icontains=palabra)
        )
        digitos = solo_digitos(palabra)
        if len(digitos) >= 3:
            condicion |= Q(telefono__contains=digitos)
        condiciones.append(condicion)
    if condiciones:
        # Sin distinguir acentos ni mayúsculas: «martinez» encuentra a «Martínez» (RI-13, RNF-07)
        ids = (
            clientes.annotate(
                _nombre=SinAcentos("nombre"),
                _paterno=SinAcentos("apellido_paterno"),
                _materno=SinAcentos("apellido_materno"),
                _mascota=SinAcentos("mascotas__nombre"),
            )
            .filter(reduce(and_, condiciones))
            .values("pk")
        )
        clientes = Cliente.objects.filter(pk__in=ids)
    return clientes.annotate(total_mascotas=Count("mascotas")).order_by(
        "apellido_paterno", "apellido_materno", "nombre", "pk"
    )


def registrar_cliente(formulario):
    """Alta de cliente (RF-01). El formulario ya exige el aviso de privacidad; la base lo vuelve a exigir."""
    with transaction.atomic():
        return formulario.save()
