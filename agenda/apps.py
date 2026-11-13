from django.apps import AppConfig


class AgendaConfig(AppConfig):
    """Componente «Agenda y citas» (Tabla 3.2) · clave de módulo AGE (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "agenda"
    verbose_name = "Agenda y citas"
