"""Rutas de la opción Recordatorios (prefijo /recordatorios/): UI-15."""

from django.urls import path

from . import views

app_name = "recordatorios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:id_recordatorio>/resultado/", views.resultado, name="resultado"),
]
