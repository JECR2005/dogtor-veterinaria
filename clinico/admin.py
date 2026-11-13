"""Registro en el sitio de administración. Solo se publica en el entorno local (Tabla 4.26)
para revisar datos ficticios; las pantallas del sistema son las del apartado 4.2."""

from django.contrib import admin

from .models import Aplicacion, Consulta, DetalleReceta, ExpedienteClinico, Receta, RegistroEstetica

for modelo in (
    ExpedienteClinico,
    Consulta,
    Aplicacion,
    Receta,
    DetalleReceta,
    RegistroEstetica,
):
    admin.site.register(modelo)
