"""Pone en todas las plantillas el menú lateral del rol del usuario (Tabla 4.4, apartado 4.4).

Reglas de uso del menú: un contador junto a Recordatorios, Inventario y Estética indica cuántos avisos
pendientes hay (S3-14). En la tableta de estética el menú del estilista se reduce a Inicio, Estética,
Agenda y Mi cuenta.
"""

from .menu import opciones_para

# Opciones que el estilista no ve en la tableta (pantallas menores a 1200 px)
SOLO_ESCRITORIO = {"Estilista": {"clientes"}}


def menu(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {"menu_opciones": [], "menu_rol": None}
    opciones = opciones_para(usuario.rol)
    contadores = contadores_del_menu(usuario, {o["clave"] for o in opciones})
    for opcion in opciones:
        opcion["contador"] = contadores.get(opcion["clave"], 0)
        opcion["solo_escritorio"] = opcion["clave"] in SOLO_ESCRITORIO.get(usuario.rol, set())
    return {"menu_opciones": opciones, "menu_rol": usuario.rol}


def contadores_del_menu(usuario, claves):
    """Pendientes por opción: recordatorios por contactar, alertas de inventario y avisos de estética."""
    from django.utils import timezone

    from seguridad.models import Rol

    hoy = timezone.localdate()
    contadores = {}
    if "recordatorios" in claves:
        from recordatorios.services import pendientes

        contadores["recordatorios"] = pendientes(hoy).count()
    if "inventario" in claves:
        from inventario.services import alertas

        contadores["inventario"] = sum(len(lista) for lista in alertas(hoy).values())
    if "estetica" in claves:
        from clinico import services as clinico

        if usuario.rol == Rol.ESTILISTA:
            citas = clinico.citas_de_estetica_del_dia(hoy, usuario.empleado)
            contadores["estetica"] = sum(cita.estado == "Programada" for cita in citas)
        else:
            contadores["estetica"] = len(clinico.avisos_pendientes())
    return contadores
