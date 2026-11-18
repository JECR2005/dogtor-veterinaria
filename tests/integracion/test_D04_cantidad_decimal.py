"""S2-02 · Decisión D-04: existencias y movimientos de inventario con 2 decimales.

Comprueba el esquema nuevo (bd/01_tablas.sql) y que el script incremental convierta una base que todavía
tiene las columnas enteras. Todo ocurre dentro de la transacción de la prueba y se revierte al terminar.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.db import connection

from bd.ejecutar import CARPETA, ejecutar_scripts
from catalogos.models import Producto
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CAMBIO = CARPETA / "cambios" / "2026-11-17_RD-05_cantidad_decimal.sql"

# Deja las dos columnas como estaban en el Sprint 0 (INT), para simular una base existente.
VOLVER_A_ENTEROS = [
    "DROP INDEX IX_lote_producto_caducidad ON dbo.lote",
    "ALTER TABLE dbo.lote DROP CONSTRAINT CK_lote_cantidad_no_negativa",
    "ALTER TABLE dbo.lote DROP CONSTRAINT DF_lote_cantidad",
    "ALTER TABLE dbo.lote ALTER COLUMN cantidad_disponible INT NOT NULL",
    "ALTER TABLE dbo.lote ADD CONSTRAINT DF_lote_cantidad DEFAULT 0 FOR cantidad_disponible",
    "ALTER TABLE dbo.lote ADD CONSTRAINT CK_lote_cantidad_no_negativa CHECK (cantidad_disponible >= 0)",
    "CREATE INDEX IX_lote_producto_caducidad ON dbo.lote (id_producto, fecha_caducidad) "
    "INCLUDE (cantidad_disponible)",
    "ALTER TABLE dbo.movimiento_inventario DROP CONSTRAINT CK_movimiento_signo_cantidad",
    "ALTER TABLE dbo.movimiento_inventario ALTER COLUMN cantidad INT NOT NULL",
    "ALTER TABLE dbo.movimiento_inventario ADD CONSTRAINT CK_movimiento_signo_cantidad CHECK ("
    "(tipo IN (N'Entrada', N'Devolución') AND cantidad > 0) "
    "OR (tipo IN (N'Venta', N'Aplicación') AND cantidad < 0) "
    "OR (tipo = N'Ajuste' AND cantidad <> 0))",
]


def _tipos():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE (TABLE_NAME = 'lote' AND COLUMN_NAME = 'cantidad_disponible') "
            "OR (TABLE_NAME = 'movimiento_inventario' AND COLUMN_NAME = 'cantidad')"
        )
        return {fila[0]: tuple(fila[1:]) for fila in cursor.fetchall()}


def _objetos_que_protegen_las_reglas():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sys.objects WHERE name IN "
            "('CK_lote_cantidad_no_negativa', 'DF_lote_cantidad', 'CK_movimiento_signo_cantidad') "
            "UNION ALL SELECT name FROM sys.indexes WHERE name = 'IX_lote_producto_caducidad'"
        )
        return {fila[0] for fila in cursor.fetchall()}


ESPERADOS = {
    "CK_lote_cantidad_no_negativa",
    "DF_lote_cantidad",
    "CK_movimiento_signo_cantidad",
    "IX_lote_producto_caducidad",
}


def test_D04_el_esquema_nuevo_guarda_existencias_con_dos_decimales(crear_usuario):
    administrador = crear_usuario("admin", rol=Rol.ADMINISTRADOR).empleado
    producto = Producto.objects.create(
        codigo="PRB-ML",
        nombre="Solución inyectable de prueba",
        categoria="Medicamento",
        unidad_medida="mL",
        precio_venta=Decimal("8"),
        stock_minimo=20,
    )
    lote = Lote.objects.create(
        producto=producto,
        numero_lote="ML-1",
        fecha_caducidad=date.today() + timedelta(days=200),
        cantidad_disponible=Decimal("100.00"),
    )
    MovimientoInventario.objects.create(
        lote=lote, empleado=administrador, tipo=TipoMovimiento.ENTRADA, cantidad=Decimal("100.00")
    )
    MovimientoInventario.objects.create(
        lote=lote,
        empleado=administrador,
        tipo=TipoMovimiento.AJUSTE,
        cantidad=Decimal("-2.50"),
        motivo="Se derramó al cargar la jeringa",
    )
    Lote.objects.filter(pk=lote.pk).update(cantidad_disponible=Decimal("97.50"))

    lote.refresh_from_db()
    assert lote.cantidad_disponible == Decimal("97.50")
    cantidades = sorted(lote.movimientos.values_list("cantidad", flat=True))
    assert cantidades == [Decimal("-2.50"), Decimal("100.00")]
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT stock_disponible FROM dbo.vista_stock_disponible WHERE id_producto = %s",
            [producto.id_producto],
        )
        assert cursor.fetchone()[0] == Decimal("97.50")
    assert _tipos() == {
        "lote": ("decimal", 10, 2),
        "movimiento_inventario": ("decimal", 10, 2),
    }


def test_D04_el_cambio_convierte_una_base_existente_y_se_puede_repetir():
    with connection.cursor() as cursor:
        for sentencia in VOLVER_A_ENTEROS:
            cursor.execute(sentencia)
    assert _tipos()["lote"][0] == "int"

    ejecutar_scripts(connection, [CAMBIO])
    assert _tipos() == {"lote": ("decimal", 10, 2), "movimiento_inventario": ("decimal", 10, 2)}
    assert _objetos_que_protegen_las_reglas() == ESPERADOS

    ejecutar_scripts(connection, [CAMBIO])  # una segunda vez no falla ni duplica nada
    assert _objetos_que_protegen_las_reglas() == ESPERADOS
