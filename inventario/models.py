"""Componente Inventario y compras (Tabla 3.2).

Tablas del diccionario: lote (3.49), movimiento_inventario (3.50), pedido_compra (3.52)
y detalle_pedido (3.53).
El stock disponible NO se almacena: lo calcula la vista dbo.vista_stock_disponible (bd/02_vistas.sql, RD-05).
El disparador TR_movimiento_inventario_inmutable impide modificar o borrar movimientos (RD-07).
"""

from django.db import models
from django.utils import timezone


class TipoMovimiento(models.TextChoices):
    ENTRADA = "Entrada", "Entrada"
    VENTA = "Venta", "Venta"
    APLICACION = "Aplicación", "Aplicación"
    DEVOLUCION = "Devolución", "Devolución"
    AJUSTE = "Ajuste", "Ajuste"


class EstadoPedido(models.TextChoices):
    PENDIENTE = "Pendiente", "Pendiente"
    RECIBIDO = "Recibido", "Recibido"
    CANCELADO = "Cancelado", "Cancelado"


# --- Tabla 3.49 · LOTE --------------------------------------------------------
class Lote(models.Model):
    id_lote = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        "catalogos.Producto", on_delete=models.PROTECT, db_column="id_producto", related_name="lotes"
    )
    numero_lote = models.CharField(max_length=30)
    fecha_caducidad = models.DateField(null=True, blank=True)
    cantidad_disponible = models.IntegerField(default=0)
    fecha_entrada = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = "lote"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.producto} · lote {self.numero_lote}"


# --- Tabla 3.50 · MOVIMIENTO_INVENTARIO ---------------------------------------
class MovimientoInventario(models.Model):
    """Registro inmodificable (RD-07): los errores se corrigen con un movimiento de Ajuste, nunca editando."""

    id_movimiento = models.AutoField(primary_key=True)
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, db_column="id_lote", related_name="movimientos")
    empleado = models.ForeignKey(
        "catalogos.Empleado",
        on_delete=models.PROTECT,
        db_column="id_empleado",
        related_name="movimientos_inventario",
    )
    tipo = models.CharField(max_length=15, choices=TipoMovimiento.choices)
    cantidad = models.IntegerField()
    fecha_hora = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=40, null=True, blank=True)
    motivo = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "movimiento_inventario"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.tipo} {self.cantidad:+d} · {self.lote}"


# --- Tabla 3.52 · PEDIDO_COMPRA -----------------------------------------------
class PedidoCompra(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(
        "catalogos.Proveedor", on_delete=models.PROTECT, db_column="id_proveedor", related_name="pedidos"
    )
    empleado = models.ForeignKey(
        "catalogos.Empleado", on_delete=models.PROTECT, db_column="id_empleado", related_name="pedidos_compra"
    )
    fecha_pedido = models.DateField(default=timezone.localdate)
    fecha_recepcion = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "pedido_compra"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"Pedido {self.id_pedido} · {self.proveedor}"


# --- Tabla 3.53 · DETALLE_PEDIDO ----------------------------------------------
class DetallePedido(models.Model):
    # Decisión D-01 (docs/decisiones.md): llave sustituta + unicidad (id_pedido, id_producto)
    id_detalle_pedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(
        PedidoCompra, on_delete=models.CASCADE, db_column="id_pedido", related_name="detalles"
    )
    producto = models.ForeignKey(
        "catalogos.Producto",
        on_delete=models.PROTECT,
        db_column="id_producto",
        related_name="detalles_pedido",
    )
    cantidad_solicitada = models.IntegerField()
    cantidad_recibida = models.IntegerField(null=True, blank=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "detalle_pedido"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.producto} × {self.cantidad_solicitada}"
