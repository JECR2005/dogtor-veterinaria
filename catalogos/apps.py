from django.apps import AppConfig


class CatalogosConfig(AppConfig):
    """Componente «Catálogos» (Tabla 3.2) · clave de módulo CAT (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "catalogos"
    verbose_name = "Catálogos"
