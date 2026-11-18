# S2-02 · Decisión D-04: existencias y movimientos con 2 decimales.
# Los modelos son managed = False (D-10): esta migración solo actualiza el estado de Django; la columna
# se cambia con bd/cambios/2026-11-17_RD-05_cantidad_decimal.sql (bases existentes) y bd/01_tablas.sql.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventario", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lote",
            name="cantidad_disponible",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name="movimientoinventario",
            name="cantidad",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
