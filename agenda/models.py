"""Componente Agenda y citas (Tabla 3.2). Tabla del diccionario: cita (3.40)."""

from django.db import models


class EstadoCita(models.TextChoices):
    PROGRAMADA = "Programada", "Programada"
    COMPLETADA = "Completada", "Completada"
    CANCELADA = "Cancelada", "Cancelada"


# --- Tabla 3.40 · CITA --------------------------------------------------------
class Cita(models.Model):
    id_cita = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(
        "catalogos.Mascota", on_delete=models.PROTECT, db_column="id_mascota", related_name="citas"
    )
    empleado = models.ForeignKey(
        "catalogos.Empleado", on_delete=models.PROTECT, db_column="id_empleado", related_name="citas"
    )
    servicio = models.ForeignKey(
        "catalogos.Servicio", on_delete=models.PROTECT, db_column="id_servicio", related_name="citas"
    )
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    estado = models.CharField(max_length=12, choices=EstadoCita.choices, default=EstadoCita.PROGRAMADA)
    motivo = models.CharField(max_length=200, null=True, blank=True)
    motivo_cancelacion = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "cita"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)
        # RD-02 (empalmes) se valida en agenda/services.py en P1, dentro de una transacción que
        # bloquea la agenda del empleado (select_for_update → WITH (UPDLOCK, ROWLOCK) en SQL Server).

    def __str__(self):
        return f"{self.fecha_hora_inicio:%Y-%m-%d %H:%M} · {self.mascota} · {self.servicio}"
