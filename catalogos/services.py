"""Servicios (reglas de negocio) del componente «Catálogos».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P1 y P2:

- RF-01: alta, edición y baja lógica de clientes con aviso de privacidad (P1).
- RF-02 y RD-10: alta de mascota que abre su único expediente clínico (P1).
- RF-03 y RD-01: empleados con horario; cédula obligatoria para el veterinario (P1).
- RF-04: catálogo de servicios con precio y duración (P1).
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction

from seguridad import bitacora
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import AccionBitacora

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
