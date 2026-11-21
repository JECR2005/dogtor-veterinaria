"""Rutas de la opción Bitácora (prefijo /bitacora/): UI-20, solo el Administrador."""

from django.urls import path

from . import views_bitacora as views

app_name = "bitacora"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("exportar/", views.exportar, name="exportar"),
    path("contactos/", views.contactos, name="contactos"),
]
