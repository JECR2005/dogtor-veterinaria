"""Rutas de la opción Ventas y caja (prefijo /ventas/): UI-17 a UI-19."""

from django.urls import path

from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nueva, name="nueva"),
    path("tickets/<int:id_venta>/", views.ticket, name="ticket"),
    path("tickets/<int:id_venta>/pagar/", views.pagar, name="pagar"),
    path("tickets/<int:id_venta>/factura/", views.factura, name="factura"),
    path("tickets/<int:id_venta>/pdf/", views.ticket_pdf, name="ticket_pdf"),
]
