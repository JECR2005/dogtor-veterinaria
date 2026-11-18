/* =============================================================================
   Dogtor: Veterinaria & Petcare · Cambio al esquema (S2-02, decisión D-04)
   2026-11-17 · RD-05 · Existencias y movimientos de inventario con 2 decimales

   Qué cambia:
     lote.cantidad_disponible        INT → DECIMAL(10,2)
     movimiento_inventario.cantidad  INT → DECIMAL(10,2)
   Por qué: aplicacion.cantidad y detalle_venta.cantidad ya admiten decimales (0.5 mL); sin este cambio
   no se podría descontar del lote lo que se aplica (D-04, opción b).

   Para una base que YA existe (la de cada integrante o la del local). Las bases nuevas ya nacen así,
   porque bd/01_tablas.sql tiene el cambio. Se puede ejecutar más de una vez sin problema.

   Ejecutar conectado a la base Dogtor:
       python bd/ejecutar.py --cambio bd/cambios/2026-11-17_RD-05_cantidad_decimal.sql
   o abrirlo en SSMS con la base Dogtor seleccionada y pulsar Ejecutar.

   Las restricciones y el índice que usan las columnas se quitan y se vuelven a crear igual que en
   01_tablas.sql, porque SQL Server no deja cambiar el tipo de una columna que los tiene.
   ============================================================================= */
SET XACT_ABORT ON;
GO

BEGIN TRANSACTION;
GO

-- 1. LOTE (Tabla 3.49) ------------------------------------------------------------
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_lote_producto_caducidad' AND object_id = OBJECT_ID(N'dbo.lote'))
    DROP INDEX IX_lote_producto_caducidad ON dbo.lote;
IF OBJECT_ID(N'dbo.CK_lote_cantidad_no_negativa', N'C') IS NOT NULL
    ALTER TABLE dbo.lote DROP CONSTRAINT CK_lote_cantidad_no_negativa;
IF OBJECT_ID(N'dbo.DF_lote_cantidad', N'D') IS NOT NULL
    ALTER TABLE dbo.lote DROP CONSTRAINT DF_lote_cantidad;
GO

ALTER TABLE dbo.lote ALTER COLUMN cantidad_disponible DECIMAL(10,2) NOT NULL;
GO

IF OBJECT_ID(N'dbo.DF_lote_cantidad', N'D') IS NULL
    ALTER TABLE dbo.lote ADD CONSTRAINT DF_lote_cantidad DEFAULT 0 FOR cantidad_disponible;
IF OBJECT_ID(N'dbo.CK_lote_cantidad_no_negativa', N'C') IS NULL
    ALTER TABLE dbo.lote ADD CONSTRAINT CK_lote_cantidad_no_negativa CHECK (cantidad_disponible >= 0);   -- RD-05
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_lote_producto_caducidad' AND object_id = OBJECT_ID(N'dbo.lote'))
    CREATE INDEX IX_lote_producto_caducidad ON dbo.lote (id_producto, fecha_caducidad) INCLUDE (cantidad_disponible);
GO

-- 2. MOVIMIENTO_INVENTARIO (Tabla 3.50) ---------------------------------------------
IF OBJECT_ID(N'dbo.CK_movimiento_signo_cantidad', N'C') IS NOT NULL
    ALTER TABLE dbo.movimiento_inventario DROP CONSTRAINT CK_movimiento_signo_cantidad;
GO

ALTER TABLE dbo.movimiento_inventario ALTER COLUMN cantidad DECIMAL(10,2) NOT NULL;
GO

IF OBJECT_ID(N'dbo.CK_movimiento_signo_cantidad', N'C') IS NULL
ALTER TABLE dbo.movimiento_inventario ADD CONSTRAINT CK_movimiento_signo_cantidad CHECK (
    (tipo IN (N'Entrada', N'Devolución') AND cantidad > 0)
    OR (tipo IN (N'Venta', N'Aplicación') AND cantidad < 0)
    OR (tipo = N'Ajuste' AND cantidad <> 0));
GO

-- 3. La vista de stock toma el tipo nuevo -------------------------------------------
IF OBJECT_ID(N'dbo.vista_stock_disponible', N'V') IS NOT NULL
    EXEC sp_refreshview N'dbo.vista_stock_disponible';
GO

IF @@TRANCOUNT > 0 COMMIT TRANSACTION;
SET XACT_ABORT OFF;
GO

PRINT N'Cambio 2026-11-17_RD-05_cantidad_decimal aplicado: existencias y movimientos con 2 decimales.';
GO
