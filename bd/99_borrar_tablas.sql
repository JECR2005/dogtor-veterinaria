/* =============================================================================
   Dogtor · 99 · Borra la vista, el disparador, las 26 tablas y las de Django  ·  SOLO DESARROLLO
   Sirve para recrear el esquema desde cero en una computadora local (después: 01, 02 y migrate).
   Lo más cómodo es `python bd/ejecutar.py --recrear`, que hace los cuatro pasos.
   NUNCA ejecutar en producción: se pierden todos los datos. Antes, haga un respaldo.
   ============================================================================= */

IF DB_NAME() NOT IN (N'Dogtor', N'test_Dogtor')
    THROW 50099, N'Este script solo se ejecuta en las bases Dogtor (local) o test_Dogtor.', 1;
-- (sin GO aquí: si la validación falla, THROW detiene todo el lote y no se borra nada)

SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    -- Tablas de Django (sesiones, historial de /admin-local/, permisos, migraciones). django_admin_log apunta a
    -- usuario, así que se borran primero; `python bd/ejecutar.py --recrear` las vuelve a crear con migrate.
    DECLARE @sql NVARCHAR(MAX) = N'';
    SELECT @sql += N'ALTER TABLE ' + QUOTENAME(SCHEMA_NAME(t.schema_id)) + N'.' + QUOTENAME(t.name)
                 + N' DROP CONSTRAINT ' + QUOTENAME(fk.name) + N'; '
    FROM sys.foreign_keys AS fk
    JOIN sys.tables AS t ON t.object_id = fk.parent_object_id
    WHERE t.name LIKE N'django[_]%' OR t.name LIKE N'auth[_]%';
    EXEC sys.sp_executesql @sql;
    SET @sql = N'';
    SELECT @sql += N'DROP TABLE ' + QUOTENAME(SCHEMA_NAME(schema_id)) + N'.' + QUOTENAME(name) + N'; '
    FROM sys.tables
    WHERE name LIKE N'django[_]%' OR name LIKE N'auth[_]%';
    EXEC sys.sp_executesql @sql;

    DROP VIEW IF EXISTS dbo.vista_stock_disponible;
    DROP TRIGGER IF EXISTS dbo.TR_movimiento_inventario_inmutable;

    -- Orden inverso al de creación, para respetar las llaves foráneas
    DROP TABLE IF EXISTS dbo.pago;
    DROP TABLE IF EXISTS dbo.detalle_venta;
    DROP TABLE IF EXISTS dbo.venta;
    DROP TABLE IF EXISTS dbo.detalle_pedido;
    DROP TABLE IF EXISTS dbo.pedido_compra;
    DROP TABLE IF EXISTS dbo.recordatorio;
    DROP TABLE IF EXISTS dbo.registro_estetica;
    DROP TABLE IF EXISTS dbo.detalle_receta;
    DROP TABLE IF EXISTS dbo.receta;
    DROP TABLE IF EXISTS dbo.aplicacion;
    DROP TABLE IF EXISTS dbo.consulta;
    DROP TABLE IF EXISTS dbo.expediente_clinico;
    DROP TABLE IF EXISTS dbo.movimiento_inventario;
    DROP TABLE IF EXISTS dbo.lote;
    DROP TABLE IF EXISTS dbo.producto;
    DROP TABLE IF EXISTS dbo.proveedor;
    DROP TABLE IF EXISTS dbo.cita;
    DROP TABLE IF EXISTS dbo.servicio;
    DROP TABLE IF EXISTS dbo.bitacora_auditoria;
    DROP TABLE IF EXISTS dbo.usuario;
    DROP TABLE IF EXISTS dbo.horario_laboral;
    DROP TABLE IF EXISTS dbo.empleado;
    DROP TABLE IF EXISTS dbo.mascota;
    DROP TABLE IF EXISTS dbo.cliente;
    DROP TABLE IF EXISTS dbo.raza;
    DROP TABLE IF EXISTS dbo.especie;

    COMMIT TRANSACTION;
    SET XACT_ABORT OFF;
END TRY
BEGIN CATCH
    -- Todo o nada: si algo falla, no se borra ninguna tabla
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET XACT_ABORT OFF;
    THROW;
END CATCH;
GO

PRINT N'Esquema de Dogtor borrado.';
GO
