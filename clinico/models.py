"""Componente Expediente clínico (Tabla 3.2).

Tablas del diccionario: expediente_clinico (3.41), consulta (3.42), aplicacion (3.43), receta (3.44),
detalle_receta (3.45) y registro_estetica (3.46).
"""

from django.db import models
from django.utils import timezone


class EstadoConsulta(models.TextChoices):
    ABIERTA = "Abierta", "Abierta"
    FIRMADA = "Firmada", "Firmada"


class TipoAplicacion(models.TextChoices):
    VACUNA = "Vacuna", "Vacuna"
    DESPARASITANTE = "Desparasitante", "Desparasitante"
    OTRO = "Otro", "Otro"


# --- Tabla 3.41 · EXPEDIENTE_CLINICO ------------------------------------------
class ExpedienteClinico(models.Model):
    id_expediente = models.AutoField(primary_key=True)
    # RD-10: un solo expediente por mascota (FK + UK)
    mascota = models.OneToOneField(
        "catalogos.Mascota", on_delete=models.PROTECT, db_column="id_mascota", related_name="expediente"
    )
    fecha_apertura = models.DateField(default=timezone.localdate)
    antecedentes = models.TextField(null=True, blank=True)
    alergias = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "expediente_clinico"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Expediente de {self.mascota}"


# --- Tabla 3.42 · CONSULTA ----------------------------------------------------
class Consulta(models.Model):
    id_consulta = models.AutoField(primary_key=True)
    expediente = models.ForeignKey(
        ExpedienteClinico, on_delete=models.PROTECT, db_column="id_expediente", related_name="consultas"
    )
    cita = models.OneToOneField(
        "agenda.Cita", on_delete=models.PROTECT, db_column="id_cita", related_name="consulta"
    )
    empleado = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        db_column="id_empleado",
        related_name="consultas_firmadas",
    )
    fecha_hora = models.DateTimeField(default=timezone.now)
    sintomas = models.TextField()
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    diagnostico = models.TextField(null=True, blank=True)
    tratamiento = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=EstadoConsulta.choices, default=EstadoConsulta.ABIERTA)
    fecha_firma = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "consulta"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Consulta {self.id_consulta} · {self.fecha_hora:%Y-%m-%d}"


# --- Tabla 3.43 · APLICACION --------------------------------------------------
class Aplicacion(models.Model):
    id_aplicacion = models.AutoField(primary_key=True)
    consulta = models.ForeignKey(
        Consulta, on_delete=models.PROTECT, db_column="id_consulta", related_name="aplicaciones"
    )
    lote = models.ForeignKey(
        "inventario.Lote", on_delete=models.PROTECT, db_column="id_lote", related_name="aplicaciones"
    )
    tipo = models.CharField(max_length=15, choices=TipoAplicacion.choices)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2)
    dosis = models.CharField(max_length=30)
    fecha_aplicacion = models.DateField(default=timezone.localdate)
    proxima_fecha = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "aplicacion"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.tipo} · {self.dosis} · {self.fecha_aplicacion}"


# --- Tabla 3.44 · RECETA ------------------------------------------------------
class Receta(models.Model):
    id_receta = models.AutoField(primary_key=True)
    # RD-08: una receta solo existe dentro de una consulta
    consulta = models.ForeignKey(
        Consulta, on_delete=models.PROTECT, db_column="id_consulta", related_name="recetas"
    )
    folio = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    indicaciones_generales = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "receta"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Receta {self.folio}"


# --- Tabla 3.45 · DETALLE_RECETA ----------------------------------------------
class DetalleReceta(models.Model):
    # Decisión D-01 (docs/decisiones.md): llave sustituta + unicidad (id_receta, id_producto)
    # en lugar de llave primaria compuesta.
    id_detalle_receta = models.AutoField(primary_key=True)
    receta = models.ForeignKey(
        Receta, on_delete=models.CASCADE, db_column="id_receta", related_name="detalles"
    )
    producto = models.ForeignKey(
        "catalogos.Producto",
        on_delete=models.PROTECT,
        db_column="id_producto",
        related_name="detalles_receta",
    )
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=50)
    duracion_dias = models.SmallIntegerField()
    indicaciones = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "detalle_receta"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.producto} · {self.dosis} · {self.frecuencia}"


# --- Tabla 3.46 · REGISTRO_ESTETICA -------------------------------------------
class RegistroEstetica(models.Model):
    id_registro = models.AutoField(primary_key=True)
    cita = models.OneToOneField(
        "agenda.Cita", on_delete=models.PROTECT, db_column="id_cita", related_name="registro_estetica"
    )
    estado_pelaje_piel = models.CharField(max_length=200)
    hallazgos = models.CharField(max_length=300, null=True, blank=True)
    aviso_veterinario = models.BooleanField(default=False)
    observaciones = models.CharField(max_length=300, null=True, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "registro_estetica"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Estética · cita {self.cita_id}"
