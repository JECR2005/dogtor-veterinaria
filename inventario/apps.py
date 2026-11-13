from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Componente «Inventario y compras» (Tabla 3.2) · clave de módulo INV (Formato LV-00)."""

    default_auto_field = "django.db.models.AutoField"
    name = "inventario"
    verbose_name = "Inventario y compras"
