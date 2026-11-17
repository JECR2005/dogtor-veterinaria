"""LV-03 punto 9 · Al cerrar sesión termina el acceso (DEF-003).

Las páginas que se ven con sesión iniciada no se guardan en la caché del navegador. Así, después de pulsar
«Cerrar sesión», el botón Atrás no vuelve a mostrar datos de clientes, citas o empleados: el navegador pide
la página de nuevo y el sistema manda a iniciar sesión.
"""

from django.utils.cache import add_never_cache_headers


class SinCacheConSesion:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        usuario = getattr(request, "user", None)
        if usuario is not None and usuario.is_authenticated:
            add_never_cache_headers(respuesta)  # Cache-Control: no-cache, no-store, must-revalidate, private
        return respuesta
