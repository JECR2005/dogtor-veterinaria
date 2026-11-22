"""Rutas del componente «Agenda y citas» (prefijo /agenda/). UI-07 (S1-13 y S1-14)."""

from django.urls import path

from . import views

app_name = "agenda"

urlpatterns = [
    path("", views.calendario, name="calendario"),
    path("eventos/", views.eventos, name="eventos"),
    path("dia/", views.dia, name="dia"),
    path("dia/pdf/", views.dia_pdf, name="dia_pdf"),
    path("nueva/", views.nueva, name="nueva"),
    path("citas/<int:id_cita>/", views.cita, name="cita"),
    path("citas/<int:id_cita>/reprogramar/", views.reprogramar, name="reprogramar"),
    path("citas/<int:id_cita>/cancelar/", views.cancelar, name="cancelar"),
    path("citas/<int:id_cita>/completar/", views.completar, name="completar"),
]
