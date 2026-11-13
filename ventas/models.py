"""Componente Ventas y caja (Tabla 3.2).

Tablas del diccionario: venta (3.54), detalle_venta (3.55) y pago (3.56).

Desnormalización deliberada (apartado 3.4): venta.total y venta.saldo se actualizan en la misma transacción
que cada partida o pago. Que un abono no exceda el saldo se valida en la transacción de cobro con la fila
de la venta bloqueada (RD-06), porque una restricción CHECK no puede consultar otra tabla.
"""

from django.db import models
from django.db.models import F, Q
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
        constraints = [
            models.CheckConstraint(condition=Q(estado__in=EstadoVenta.values), name="venta_estado_ck"),
            models.CheckConstraint(condition=Q(total__gte=0), name="venta_total_ck"),
            # RD-06: el saldo nunca es negativo ni mayor que el total
            models.CheckConstraint(condition=Q(saldo__gte=0, saldo__lte=F("total")), name="venta_saldo_ck"),
            # RF-13: el ticket pasa a «Pagada» solo con saldo cero
            models.CheckConstraint(
                condition=~Q(estado=EstadoVenta.PAGADA) | Q(saldo=0), name="venta_pagada_saldo_cero_ck"
            ),
            # RF-14: la cancelación registra motivo y quién canceló
            models.CheckConstraint(
                condition=~Q(estado=EstadoVenta.CANCELADA)
                | (
                    Q(motivo_cancelacion__isnull=False) & ~Q(motivo_cancelacion="") & Q(cancelo__isnull=False)
                ),
                name="venta_cancelada_con_motivo_ck",
            ),
        ]

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
        constraints = [
            models.UniqueConstraint(fields=["venta", "numero_linea"], name="detalle_venta_venta_linea_uk"),
            # Exactamente uno de producto o servicio (apartado 3.4)
            models.CheckConstraint(
                condition=(
                    Q(producto__isnull=False, servicio__isnull=True)
                    | Q(producto__isnull=True, servicio__isnull=False)
                ),
                name="detalle_venta_producto_o_servicio_ck",
            ),
            # RD-12: el folio de receta solo acompaña a un producto
            models.CheckConstraint(
                condition=Q(receta__isnull=True) | Q(producto__isnull=False),
                name="detalle_venta_receta_producto_ck",
            ),
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="detalle_venta_cantidad_ck"),
            models.CheckConstraint(condition=Q(precio_unitario__gte=0), name="detalle_venta_precio_ck"),
            models.CheckConstraint(condition=Q(subtotal__gte=0), name="detalle_venta_subtotal_ck"),
        ]

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
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=TipoPago.values), name="pago_tipo_ck"),
            models.CheckConstraint(condition=Q(metodo__in=MetodoPago.values), name="pago_metodo_ck"),
            models.CheckConstraint(condition=Q(monto__gt=0), name="pago_monto_positivo_ck"),
            # RD-06: cambio = monto_recibido − monto, y nunca negativo
            models.CheckConstraint(
                condition=(
                    Q(monto_recibido__isnull=True, cambio__isnull=True)
                    | Q(
                        monto_recibido__isnull=False,
                        monto_recibido__gte=F("monto"),
                        cambio=F("monto_recibido") - F("monto"),
                    )
                ),
                name="pago_cambio_ck",
            ),
        ]

    def __str__(self):
        return f"{self.tipo} {self.metodo} ${self.monto}"
