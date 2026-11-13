"""Componente Agenda y citas (Tabla 3.2). Tabla del diccionario: cita (3.40)."""

from django.db import models
from django.db.models import F, Q


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
        # RNF-05: búsqueda de la agenda por empleado y fecha (Tabla 4.6.1, índices recomendados)
        indexes = [models.Index(fields=["empleado", "fecha_hora_inicio"], name="cita_empleado_inicio_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(estado__in=EstadoCita.values), name="cita_estado_ck"),
            models.CheckConstraint(
                condition=Q(fecha_hora_fin__gt=F("fecha_hora_inicio")), name="cita_fin_mayor_inicio_ck"
            ),
            # RF-05: el motivo es obligatorio al cancelar
            models.CheckConstraint(
                condition=~Q(estado=EstadoCita.CANCELADA)
                | (Q(motivo_cancelacion__isnull=False) & ~Q(motivo_cancelacion="")),
                name="cita_cancelada_con_motivo_ck",
            ),
        ]
        # RD-02 (empalmes) se valida en agenda/services.py en P1. Opcional: restricción de exclusión
        # de PostgreSQL sobre empleado y rango de tiempo para citas no canceladas (Tabla 4.27).

    def __str__(self):
        return f"{self.fecha_hora_inicio:%Y-%m-%d %H:%M} · {self.mascota} · {self.servicio}"
