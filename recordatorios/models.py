"""Componente Recordatorios (Tabla 3.2). Tabla del diccionario: recordatorio (3.47)."""

from django.db import models


class TipoRecordatorio(models.TextChoices):
    PROXIMA_DOSIS = "Próxima dosis", "Próxima dosis"
    CITA = "Cita", "Cita"


class EstadoRecordatorio(models.TextChoices):
    PENDIENTE = "Pendiente", "Pendiente"
    CONTACTADO = "Contactado", "Contactado"
    SIN_RESPUESTA = "Sin respuesta", "Sin respuesta"


# --- Tabla 3.47 · RECORDATORIO ------------------------------------------------
class Recordatorio(models.Model):
    id_recordatorio = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "catalogos.Cliente", on_delete=models.PROTECT, db_column="id_cliente", related_name="recordatorios"
    )
    aplicacion = models.ForeignKey(
        "clinico.Aplicacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_aplicacion",
        related_name="recordatorios",
    )
    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_cita",
        related_name="recordatorios",
    )
    tipo = models.CharField(max_length=15, choices=TipoRecordatorio.choices)
    fecha_objetivo = models.DateField()
    estado = models.CharField(
        max_length=15, choices=EstadoRecordatorio.choices, default=EstadoRecordatorio.PENDIENTE
    )
    empleado = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_empleado",
        related_name="recordatorios_atendidos",
    )
    fecha_contacto = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recordatorio"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.tipo} · {self.cliente} · {self.fecha_objetivo}"
