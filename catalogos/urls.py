"""Rutas del componente «Catálogos» (prefijo /clientes/). UI-05 en S1-08; UI-06 en S1-09."""

from django.urls import path

from . import views

app_name = "catalogos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:id_cliente>/", views.ficha, name="ficha"),
    path("<int:id_cliente>/editar/", views.editar, name="editar"),
    path("<int:id_cliente>/baja/confirmar/", views.confirmar_baja, name="confirmar_baja"),
    path("<int:id_cliente>/baja/", views.baja, name="baja"),
    path("<int:id_cliente>/mascotas/nueva/", views.nueva_mascota, name="nueva_mascota"),
    path("mascotas/<int:id_mascota>/", views.mascota, name="mascota"),
    path("mascotas/<int:id_mascota>/editar/", views.editar_mascota, name="editar_mascota"),
]
