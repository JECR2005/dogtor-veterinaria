"""Rutas de la opción Consulta clínica (prefijo /clinica/): UI-11 a UI-14."""

from django.urls import path

from . import views

app_name = "clinico"

urlpatterns = [
    path("", views.dia, name="dia"),
    path("citas/<int:id_cita>/atender/", views.atender, name="atender"),
    path("consultas/<int:id_consulta>/", views.consulta, name="consulta"),
    path("consultas/<int:id_consulta>/firmar/", views.firmar, name="firmar"),
    path("consultas/<int:id_consulta>/aplicar/", views.aplicar, name="aplicar"),
    path("aplicaciones/<int:id_aplicacion>/quitar/", views.quitar_aplicacion, name="quitar_aplicacion"),
    path("consultas/<int:id_consulta>/receta/", views.receta, name="receta"),
    path("recetas/<int:id_receta>/pdf/", views.receta_pdf, name="receta_pdf"),
    path("mascotas/<int:id_mascota>/historial/", views.historial, name="historial"),
]
