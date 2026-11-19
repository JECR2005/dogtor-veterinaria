"""Rutas de la opción Consulta clínica (prefijo /clinica/): UI-11 a UI-14."""

from django.urls import path

from . import views

app_name = "clinico"

urlpatterns = [
    path("", views.dia, name="dia"),
    path("citas/<int:id_cita>/atender/", views.atender, name="atender"),
    path("consultas/<int:id_consulta>/", views.consulta, name="consulta"),
    path("consultas/<int:id_consulta>/firmar/", views.firmar, name="firmar"),
    path("mascotas/<int:id_mascota>/historial/", views.historial, name="historial"),
]
