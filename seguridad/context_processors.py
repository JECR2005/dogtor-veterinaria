"""Pone en todas las plantillas el menú lateral del rol del usuario (Tabla 4.4, apartado 4.4)."""

from .menu import opciones_para


def menu(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {"menu_opciones": [], "menu_rol": None}
    return {"menu_opciones": opciones_para(usuario.rol), "menu_rol": usuario.rol}
