from django.apps import AppConfig


class RecordatoriosConfig(AppConfig):
    """Componente «Recordatorios» (Tabla 3.2) · clave de módulo REC (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "recordatorios"
    verbose_name = "Recordatorios"
