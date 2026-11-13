from django.apps import AppConfig


class VentasConfig(AppConfig):
    """Componente «Ventas y caja» (Tabla 3.2) · clave de módulo VEN (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "ventas"
    verbose_name = "Ventas y caja"
