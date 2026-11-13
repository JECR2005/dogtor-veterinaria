"""Componente Ventas y caja (Tabla 3.2).

Tablas del diccionario: venta (3.54), detalle_venta (3.55) y pago (3.56).

Desnormalización deliberada (apartado 3.4): venta.total y venta.saldo se actualizan en la misma transacción
que cada partida o pago. Que un abono no exceda el saldo se valida en la transacción de cobro con la fila
de la venta bloqueada (RD-06), porque una restricción CHECK no puede consultar otra tabla.
"""

from django.db import models
from django.utils import timezone


class EstadoVenta(models.TextChoices):
    PENDIENTE = "Pendiente", "Pendiente"
    PAGADA = "Pagada", "Pagada"
    CANCELADA = "Cancelada", "Cancelada"


class TipoPago(models.TextChoices):
    ABONO = "Abono", "Abono"
    DEVOLUCION = "Devolución", "Devolución"


class MetodoPago(models.TextChoices):
    EFECTIVO = "Efectivo", "Efectivo"
    TARJETA = "Tarjeta", "Tarjeta"
    TRANSFERENCIA = "Transferencia", "Transferencia"


# --- Tabla 3.54 · VENTA -------------------------------------------------------
class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    folio_ticket = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(
        "catalogos.Cliente", on_delete=models.PROTECT, db_column="id_cliente", related_name="ventas"
    )
    empleado = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        db_column="id_empleado",
        related_name="ventas_generadas",
    )
    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_cita",
        related_name="ventas",
    )
    fecha_hora = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=EstadoVenta.choices, default=EstadoVenta.PENDIENTE)
    requiere_factura = models.BooleanField(default=False)
    motivo_cancelacion = models.CharField(max_length=150, null=True, blank=True)
    cancelo = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_cancelo",
        related_name="ventas_canceladas",
    )

    class Meta:
        db_table = "venta"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Ticket {self.folio_ticket}"


# --- Tabla 3.55 · DETALLE_VENTA -----------------------------------------------
class DetalleVenta(models.Model):
    # Decisión D-01 (docs/decisiones.md): llave sustituta + unicidad (id_venta, numero_linea)
    id_detalle_venta = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, db_column="id_venta", related_name="detalles")
    numero_linea = models.PositiveSmallIntegerField()
    producto = models.ForeignKey(
        "catalogos.Producto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_producto",
        related_name="detalles_venta",
    )
    servicio = models.ForeignKey(
        "catalogos.Servicio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_servicio",
        related_name="detalles_venta",
    )
    receta = models.ForeignKey(
        "clinico.Receta",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_receta",
        related_name="lineas_venta",
    )
    cantidad = models.DecimalField(max_digits=8, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # RD-11: precio histórico
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_venta"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.venta} · línea {self.numero_linea}"


# --- Tabla 3.56 · PAGO --------------------------------------------------------
class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, db_column="id_venta", related_name="pagos")
    empleado = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        db_column="id_empleado",
        related_name="pagos_registrados",
    )
    tipo = models.CharField(max_length=10, choices=TipoPago.choices)
    metodo = models.CharField(max_length=15, choices=MetodoPago.choices)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cambio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        db_table = "pago"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.tipo} {self.metodo} ${self.monto}"
