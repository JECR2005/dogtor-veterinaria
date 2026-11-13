"""Registro en el sitio de administración. Solo se publica en el entorno local (Tabla 4.26)
para revisar datos ficticios; las pantallas del sistema son las del apartado 4.2."""

from django.contrib import admin

from .models import Recordatorio

for modelo in (Recordatorio,):
    admin.site.register(modelo)
