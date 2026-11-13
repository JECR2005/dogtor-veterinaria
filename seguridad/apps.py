from django.apps import AppConfig


class SeguridadConfig(AppConfig):
    """Componente «Seguridad y acceso» (Tabla 3.2) · clave de módulo SEG (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "seguridad"
    verbose_name = "Seguridad y acceso"
