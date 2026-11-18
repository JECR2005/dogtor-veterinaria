"""Rutas de UI-03 Empleados y usuarios (prefijo /administracion/empleados/)."""

from django.urls import path

from . import views_empleados as views

app_name = "empleados"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:id_empleado>/", views.editar, name="editar"),
]
