"""Rutas del componente «Seguridad y acceso» (prefijo /cuenta/)."""

from django.urls import path

from . import views

app_name = "seguridad"

urlpatterns = [
    path("entrar/", views.entrar, name="entrar"),
    path("salir/", views.salir, name="salir"),
    path("contrasena/", views.cambiar_contrasena, name="cambiar_contrasena"),
    path("bloqueadas/", views.cuentas_bloqueadas, name="cuentas_bloqueadas"),
    path("bloqueadas/<int:id_usuario>/reactivar/", views.reactivar, name="reactivar"),
]
