"""Componente Recordatorios (Tabla 3.2). Tabla del diccionario: recordatorio (3.47)."""

from django.db import models
from django.db.models import Q


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
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=TipoRecordatorio.values), name="recordatorio_tipo_ck"
            ),
            models.CheckConstraint(
                condition=Q(estado__in=EstadoRecordatorio.values), name="recordatorio_estado_ck"
            ),
            # Exactamente uno de aplicación o cita, y coherente con el tipo (apartado 3.4)
            models.CheckConstraint(
                condition=(
                    Q(tipo=TipoRecordatorio.PROXIMA_DOSIS, aplicacion__isnull=False, cita__isnull=True)
                    | Q(tipo=TipoRecordatorio.CITA, cita__isnull=False, aplicacion__isnull=True)
                ),
                name="recordatorio_origen_unico_ck",
            ),
            # RF-09: al marcarlo «Contactado» se registra quién y cuándo
            models.CheckConstraint(
                condition=~Q(estado=EstadoRecordatorio.CONTACTADO)
                | Q(empleado__isnull=False, fecha_contacto__isnull=False),
                name="recordatorio_contacto_registrado_ck",
            ),
        ]

    def __str__(self):
        return f"{self.tipo} · {self.cliente} · {self.fecha_objetivo}"
