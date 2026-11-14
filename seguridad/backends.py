"""Autenticación de Django conectada a las reglas de RNF-01.

Todo inicio de sesión (la pantalla UI-01 y el sitio de administración del entorno local) pasa por
`services.autenticar`, así que el bloqueo al quinto intento aplica en cualquier entrada.
"""

from django.contrib.auth.backends import BaseBackend

from . import services
from .models import Usuario


class BackendDogtor(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        nombre = username if username is not None else kwargs.get(Usuario.USERNAME_FIELD)
        if nombre is None or password is None:
            return None
        resultado = services.autenticar(nombre, password)
        if request is not None:
            request.resultado_autenticacion = resultado
        return resultado.usuario if resultado.aceptado else None

    def get_user(self, user_id):
        try:
            usuario = Usuario.objects.select_related("empleado").get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
        # Una cuenta dada de baja o bloqueada pierde la sesión que tuviera abierta
        if not usuario.is_active or usuario.esta_bloqueado:
            return None
        return usuario
