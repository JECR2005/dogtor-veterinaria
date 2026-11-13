"""Rutas del sistema Dogtor. Cada componente publica sus pantallas en su propio urls.py."""

from django.conf import settings
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("salud/", views.salud, name="salud"),
    path("cuenta/", include("seguridad.urls")),
    path("clientes/", include("catalogos.urls")),
    path("agenda/", include("agenda.urls")),
    path("clinica/", include("clinico.urls")),
    path("inventario/", include("inventario.urls")),
    path("ventas/", include("ventas.urls")),
    path("recordatorios/", include("recordatorios.urls")),
    path("reportes/", include("reportes.urls")),
]

# El sitio de administración de Django solo se publica en el entorno local (Tabla 4.26)
if getattr(settings, "DOGTOR_ADMIN_HABILITADO", False):
    from django.contrib import admin

    urlpatterns.append(path("admin-local/", admin.site.urls))
