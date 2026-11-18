"""Rutas de UI-04 Catálogo de servicios (prefijo /administracion/servicios/)."""

from django.urls import path

from . import views_servicios as views

app_name = "servicios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:id_servicio>/", views.editar, name="editar"),
]
