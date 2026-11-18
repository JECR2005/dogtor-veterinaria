"""S1-05 · Permiso del rol validado en cada vista (RNF-01, RI-11, Tabla 4.9).

El menú oculta lo que un rol no usa, pero ocultar un botón no protege el dato: cada vista se declara
con `@requiere_permiso("<opción del menú>")` y el servidor revisa el permiso en cada solicitud,
aunque la dirección se escriba a mano.

- Sin sesión → pantalla de inicio de sesión.
- Sin la opción en su rol → «Acceso denegado» (403).
- Con nivel de consulta (○) → puede ver (GET); guardar, cambiar o borrar (POST, PUT, PATCH, DELETE)
  exige nivel completo (●).

La prueba tests/integracion/test_permisos.py recorre todas las rutas y falla si una vista nueva no
declara su permiso, así ninguna pantalla queda abierta por olvido.
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .menu import NIVEL_COMPLETO, NIVEL_CONSULTA, nivel_de_acceso

METODOS_DE_CONSULTA = frozenset({"GET", "HEAD", "OPTIONS"})

# Vistas abiertas a propósito; cualquier otra debe declarar su permiso
VISTAS_PUBLICAS = frozenset({"seguridad:entrar", "seguridad:salir", "salud"})


def nivel_requerido(metodo, nivel=None):
    """Nivel que exige una solicitud: el indicado o, si no se indica, según el método HTTP."""
    if nivel is not None:
        return nivel
    return NIVEL_CONSULTA if metodo in METODOS_DE_CONSULTA else NIVEL_COMPLETO


def requiere_permiso(opcion, nivel=None):
    """Decorador de vistas. `opcion` es la clave de la Tabla 4.9 (por ejemplo "agenda").

    `nivel=None` deja que el método decida (consulta para ver, completo para modificar);
    `nivel=NIVEL_COMPLETO` exige el nivel completo incluso para ver la pantalla.
    """
    nivel_de_acceso("Administrador", opcion)  # falla al importar si la opción no existe en el menú
    if nivel not in (None, NIVEL_CONSULTA, NIVEL_COMPLETO):
        raise ValueError(f"Nivel desconocido: {nivel}")

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = request.user
            if not usuario.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not usuario.tiene_permiso(opcion, nivel_requerido(request.method, nivel)):
                raise PermissionDenied
            # Las plantillas usan el nivel para mostrar u ocultar los botones de modificar
            request.dogtor_opcion = opcion
            request.dogtor_nivel = nivel_de_acceso(usuario.rol, opcion)
            return vista(request, *args, **kwargs)

        envoltura.dogtor_permiso = (opcion, nivel)
        return envoltura

    return decorador
