"""Rutas de la opción Estética (prefijo /estetica/): UI-16."""

from django.urls import path

from . import views_estetica as views

app_name = "estetica"

urlpatterns = [
    path("", views.dia, name="dia"),
    path("citas/<int:id_cita>/atender/", views.atender, name="atender"),
    path("registros/<int:id_registro>/", views.registro, name="registro"),
]
