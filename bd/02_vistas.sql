/* =============================================================================
   Dogtor · 02 · Vistas
   Ejecutar conectado a la base Dogtor después de 01_tablas.sql. Se puede ejecutar de nuevo sin borrar nada.
   ============================================================================= */

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* RD-05: el stock disponible NO se almacena; es la suma de las existencias de los lotes no vencidos.
   Un lote que caduca hoy todavía se puede usar (RD-03 bloquea los lotes cuya caducidad «ya pasó»).
   También da los datos de las alertas de RF-11: stock bajo el mínimo y caducidad en 30 días o menos. */
CREATE OR ALTER VIEW dbo.vista_stock_disponible
AS
SELECT
    p.id_producto,
    p.codigo,
    p.nombre,
    p.categoria,
    p.stock_minimo,
    COALESCE(SUM(CASE WHEN l.fecha_caducidad IS NULL OR l.fecha_caducidad >= CAST(GETDATE() AS DATE)
                      THEN l.cantidad_disponible END), 0) AS stock_disponible,
    MIN(CASE WHEN l.cantidad_disponible > 0 AND l.fecha_caducidad >= CAST(GETDATE() AS DATE)
             THEN l.fecha_caducidad END) AS proxima_caducidad,
    CAST(CASE WHEN COALESCE(SUM(CASE WHEN l.fecha_caducidad IS NULL OR l.fecha_caducidad >= CAST(GETDATE() AS DATE)
                                     THEN l.cantidad_disponible END), 0) < p.stock_minimo
              THEN 1 ELSE 0 END AS BIT) AS bajo_minimo,
    CAST(CASE WHEN MIN(CASE WHEN l.cantidad_disponible > 0 AND l.fecha_caducidad >= CAST(GETDATE() AS DATE)
                            THEN l.fecha_caducidad END) <= DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
              THEN 1 ELSE 0 END AS BIT) AS caduca_en_30_dias
FROM dbo.producto AS p
LEFT JOIN dbo.lote AS l ON l.id_producto = p.id_producto
WHERE p.activo = 1
GROUP BY p.id_producto, p.codigo, p.nombre, p.categoria, p.stock_minimo;
GO

PRINT N'Vista vista_stock_disponible lista.';
GO
