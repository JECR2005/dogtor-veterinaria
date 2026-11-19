"""Rutas de la opción Compras (prefijo /compras/): UI-09 Proveedores y pedidos, UI-10 Recepción de pedido."""

from django.urls import path

from . import views_compras as views

app_name = "compras"

urlpatterns = [
    path("proveedores/", views.proveedores, name="proveedores"),
    path("proveedores/nuevo/", views.proveedor_nuevo, name="proveedor_nuevo"),
    path("proveedores/<int:id_proveedor>/editar/", views.proveedor_editar, name="proveedor_editar"),
    path("pedidos/", views.pedidos, name="pedidos"),
    path("pedidos/nuevo/", views.pedido_nuevo, name="pedido_nuevo"),
    path("pedidos/<int:id_pedido>/", views.pedido, name="pedido"),
    path("pedidos/<int:id_pedido>/editar/", views.pedido_editar, name="pedido_editar"),
    path("pedidos/<int:id_pedido>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),
    path("pedidos/<int:id_pedido>/recibir/", views.pedido_recibir, name="pedido_recibir"),
]
