"""Rutas de la opción Inventario (prefijo /inventario/): UI-08 Productos, lotes y alertas."""

from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("productos/", views.productos, name="productos"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:id_producto>/editar/", views.producto_editar, name="producto_editar"),
]
