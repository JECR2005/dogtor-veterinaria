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
    # D-04: con 2 decimales, para descontar aplicaciones fraccionarias (0.5 mL)
    cantidad_disponible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_entrada = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = "lote"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.producto} · lote {self.numero_lote}"

    def esta_vencido(self, hoy=None):
        """RD-03 (TU-06): vence al terminar el día de su caducidad; el que caduca hoy todavía es vigente."""
        if self.fecha_caducidad is None:
            return False
        return self.fecha_caducidad < (hoy or timezone.localdate())

    def estado(self, hoy=None):
        """Estado para mostrar (RI-02): Agotado, Vencido, Por caducar (30 días o menos) o Vigente.

        Un lote sin existencias es «Agotado» aunque ya haya caducado: no queda nada que vender ni desechar.
        """
        hoy = hoy or timezone.localdate()
        if self.cantidad_disponible <= 0:
            return "Agotado"
        if self.esta_vencido(hoy):
            return "Vencido"
        if self.fecha_caducidad and (self.fecha_caducidad - hoy).days <= 30:
            return "Por caducar"
        return "Vigente"


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
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)  # con signo (D-04)
    fecha_hora = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=40, null=True, blank=True)
    motivo = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "movimiento_inventario"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.tipo} {self.cantidad:+} · {self.lote}"


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
        return f"Pedido {self.folio} · {self.proveedor}"

    @property
    def folio(self):
        """Folio para mostrar y para la referencia de los movimientos de entrada: PC-0001."""
        return f"PC-{self.id_pedido:04d}"


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
