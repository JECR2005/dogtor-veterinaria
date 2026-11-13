from django.apps import AppConfig


class ClinicoConfig(AppConfig):
    """Componente «Expediente clínico» (Tabla 3.2) · clave de módulo EXP (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "clinico"
    verbose_name = "Expediente clínico"
