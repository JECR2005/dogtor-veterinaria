"""Rutas de la opción Compras (prefijo /compras/): UI-09 Proveedores y pedidos, UI-10 Recepción de pedido."""

from django.urls import path

from . import views_compras as views

app_name = "compras"

urlpatterns = [
    path("proveedores/", views.proveedores, name="proveedores"),
    path("proveedores/nuevo/", views.proveedor_nuevo, name="proveedor_nuevo"),
    path("proveedores/<int:id_proveedor>/editar/", views.proveedor_editar, name="proveedor_editar"),
]
