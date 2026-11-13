/* =============================================================================
   Dogtor · 03 · Prueba del esquema (TS de base de datos)
   Ejecutar conectado a la base Dogtor DESPUÉS de 01_tablas.sql y 02_vistas.sql.
   Cada prueba corre en su propia transacción y se revierte: NO deja datos en la base.
   Resultado: una tabla con PASA / FALLA por prueba y un resumen al final.
   ============================================================================= */

SET NOCOUNT ON;
SET XACT_ABORT OFF;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID(N'tempdb..#resultados') IS NOT NULL DROP TABLE #resultados;
CREATE TABLE #resultados (
    n          INT IDENTITY(1,1),
    prueba     NVARCHAR(200),
    resultado  NVARCHAR(10),
    detalle    NVARCHAR(600)
);
GO

IF OBJECT_ID(N'tempdb..#probar_rechazo') IS NOT NULL DROP PROCEDURE #probar_rechazo;
GO
/* Ejecuta @sql en una transacción propia y espera que la base lo RECHACE con uno de @errores_esperados
   (547 = CHECK o FK, 2601 = índice único, 2627 = restricción UNIQUE, 50000 = error del disparador).
   Con @transaccion_viva = 1 además exige que la transacción siga utilizable (XACT_STATE() = 1). */
CREATE PROCEDURE #probar_rechazo
    @prueba NVARCHAR(200), @sql NVARCHAR(MAX), @errores_esperados NVARCHAR(50), @transaccion_viva BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT OFF;
    DECLARE @res NVARCHAR(10) = N'FALLA', @det NVARCHAR(600), @num INT, @estado INT;
    BEGIN TRANSACTION;
    BEGIN TRY
        EXEC sp_executesql @sql;
        SET @det = N'La base ACEPTÓ la operación (debía rechazarla)';
    END TRY
    BEGIN CATCH
        SELECT @num = ERROR_NUMBER(), @estado = XACT_STATE();
        SET @det = CONCAT(N'Error ', @num, N': ', ERROR_MESSAGE());
        IF CHARINDEX(CONCAT(N',', @num, N','), CONCAT(N',', @errores_esperados, N',')) > 0
           AND (@transaccion_viva = 0 OR @estado = 1)
            SET @res = N'PASA';
        IF @transaccion_viva = 1
            SET @det = CONCAT(@det, N' · XACT_STATE = ', @estado, N' (1 = transacción sigue viva)');
    END CATCH;
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    INSERT #resultados (prueba, resultado, detalle) VALUES (@prueba, @res, @det);
END;
GO

/* ---------- 1. Estructura ---------- */
INSERT #resultados (prueba, resultado, detalle)
SELECT N'Existen las 26 tablas del diccionario',
       CASE WHEN COUNT(*) = 26 THEN N'PASA' ELSE N'FALLA' END, CONCAT(COUNT(*), N' de 26')
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = N'dbo' AND TABLE_TYPE = N'BASE TABLE' AND TABLE_NAME IN (
    N'cliente', N'especie', N'raza', N'mascota', N'empleado', N'horario_laboral', N'usuario', N'servicio',
    N'cita', N'expediente_clinico', N'consulta', N'aplicacion', N'receta', N'detalle_receta',
    N'registro_estetica', N'recordatorio', N'producto', N'lote', N'movimiento_inventario', N'proveedor',
    N'pedido_compra', N'detalle_pedido', N'venta', N'detalle_venta', N'pago', N'bitacora_auditoria');

INSERT #resultados (prueba, resultado, detalle)
SELECT N'Existen la vista de stock y el disparador RD-07',
       CASE WHEN OBJECT_ID(N'dbo.vista_stock_disponible', N'V') IS NOT NULL
             AND OBJECT_ID(N'dbo.TR_movimiento_inventario_inmutable', N'TR') IS NOT NULL THEN N'PASA' ELSE N'FALLA' END,
       N'vista_stock_disponible y TR_movimiento_inventario_inmutable';

INSERT #resultados (prueba, resultado, detalle)
SELECT N'Restricciones con nombre creadas',
       CASE WHEN COUNT(*) >= 150 THEN N'PASA' ELSE N'FALLA' END,
       CONCAT(SUM(CASE WHEN type = 'PK' THEN 1 ELSE 0 END), N' PK · ',
              SUM(CASE WHEN type = 'F'  THEN 1 ELSE 0 END), N' FK · ',
              SUM(CASE WHEN type = 'UQ' THEN 1 ELSE 0 END), N' UQ · ',
              SUM(CASE WHEN type = 'C'  THEN 1 ELSE 0 END), N' CHECK · ',
              SUM(CASE WHEN type = 'D'  THEN 1 ELSE 0 END), N' DEFAULT')
FROM sys.objects WHERE type IN ('PK', 'F', 'UQ', 'C', 'D') AND SCHEMA_NAME(schema_id) = N'dbo';
GO

/* ---------- 2. Reglas que la base debe rechazar ---------- */
EXEC #probar_rechazo N'RD-01 · Veterinario sin cédula', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Sin cédula'', N''Veterinario'', ''2026-01-01'');', N'547';

EXEC #probar_rechazo N'RF-01 · Cliente sin aceptar el aviso de privacidad', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad)
    VALUES (N''Prueba'', N''Sin aviso'', N''8330000000'', N''Teléfono'', 0);', N'547';

EXEC #probar_rechazo N'Valores permitidos · Canal de contacto inexistente', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad)
    VALUES (N''Prueba'', N''Canal'', N''8330000000'', N''Paloma'', 1);', N'547';

EXEC #probar_rechazo N'RD-02 · Horario con salida antes de la entrada', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Horario'', N''Estilista'', ''2026-01-01'');
    INSERT dbo.horario_laboral (id_empleado, dia_semana, hora_entrada, hora_salida) VALUES (SCOPE_IDENTITY(), 1, ''19:00'', ''09:00'');', N'547';

EXEC #probar_rechazo N'RD-04 · Servicio de estética asignado a veterinario', N'
    INSERT dbo.servicio (nombre, categoria, precio, duracion_min, puesto_requerido) VALUES (N''Baño'', N''Estética'', 350, 60, N''Veterinario'');', N'547';

EXEC #probar_rechazo N'RD-05 · Existencias negativas en un lote', N'
    INSERT dbo.producto (codigo, nombre, categoria, unidad_medida, precio_venta) VALUES (N''PRB-1'', N''Prueba'', N''Insumo'', N''Pieza'', 10);
    INSERT dbo.lote (id_producto, numero_lote, cantidad_disponible) VALUES (SCOPE_IDENTITY(), N''L1'', -1);', N'547';

EXEC #probar_rechazo N'Movimiento de venta con cantidad positiva', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Admin'', N''Administrador'', ''2026-01-01'');
    DECLARE @e INT = SCOPE_IDENTITY();
    INSERT dbo.producto (codigo, nombre, categoria, unidad_medida, precio_venta) VALUES (N''PRB-2'', N''Prueba'', N''Insumo'', N''Pieza'', 10);
    INSERT dbo.lote (id_producto, numero_lote, cantidad_disponible) VALUES (SCOPE_IDENTITY(), N''L1'', 5);
    INSERT dbo.movimiento_inventario (id_lote, id_empleado, tipo, cantidad) VALUES (SCOPE_IDENTITY(), @e, N''Venta'', 3);', N'547';

EXEC #probar_rechazo N'RF-13 · Ticket «Pagada» con saldo pendiente', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad) VALUES (N''P'', N''V'', N''8330000000'', N''Correo'', 1);
    DECLARE @c INT = SCOPE_IDENTITY();
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Caja'', N''Recepcionista'', ''2026-01-01'');
    INSERT dbo.venta (folio_ticket, id_cliente, id_empleado, total, saldo, estado) VALUES (N''T-PRB'', @c, SCOPE_IDENTITY(), 100, 50, N''Pagada'');', N'547';

EXEC #probar_rechazo N'RD-06 · Cambio mal calculado (500 − 350 ≠ 100)', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad) VALUES (N''P'', N''V'', N''8330000000'', N''Correo'', 1);
    DECLARE @c INT = SCOPE_IDENTITY();
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Caja'', N''Recepcionista'', ''2026-01-01'');
    DECLARE @e INT = SCOPE_IDENTITY();
    INSERT dbo.venta (folio_ticket, id_cliente, id_empleado, total, saldo) VALUES (N''T-PRB'', @c, @e, 350, 350);
    INSERT dbo.pago (id_venta, id_empleado, tipo, metodo, monto, monto_recibido, cambio) VALUES (SCOPE_IDENTITY(), @e, N''Abono'', N''Efectivo'', 350, 500, 100);', N'547';

EXEC #probar_rechazo N'Partida de ticket sin producto ni servicio', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad) VALUES (N''P'', N''V'', N''8330000000'', N''Correo'', 1);
    DECLARE @c INT = SCOPE_IDENTITY();
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Caja'', N''Recepcionista'', ''2026-01-01'');
    INSERT dbo.venta (folio_ticket, id_cliente, id_empleado, total, saldo) VALUES (N''T-PRB'', @c, SCOPE_IDENTITY(), 0, 0);
    INSERT dbo.detalle_venta (id_venta, numero_linea, cantidad, precio_unitario, subtotal) VALUES (SCOPE_IDENTITY(), 1, 1, 10, 10);', N'547';

EXEC #probar_rechazo N'RD-10 · Segundo expediente para la misma mascota', N'
    INSERT dbo.cliente (nombre, apellido_paterno, telefono, preferencia_contacto, acepto_aviso_privacidad) VALUES (N''P'', N''M'', N''8330000000'', N''Correo'', 1);
    DECLARE @c INT = SCOPE_IDENTITY();
    INSERT dbo.especie (nombre) VALUES (N''Especie de prueba'');
    INSERT dbo.raza (id_especie, nombre) VALUES (SCOPE_IDENTITY(), N''Raza de prueba'');
    INSERT dbo.mascota (id_cliente, id_raza, nombre, sexo) VALUES (@c, SCOPE_IDENTITY(), N''Firulais'', N''M'');
    DECLARE @m INT = SCOPE_IDENTITY();
    INSERT dbo.expediente_clinico (id_mascota) VALUES (@m);
    INSERT dbo.expediente_clinico (id_mascota) VALUES (@m);', N'2627';

EXEC #probar_rechazo N'D-12 · Cédula profesional repetida', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, cedula_profesional, fecha_ingreso) VALUES (N''Vet'', N''Uno'', N''Veterinario'', N''CED-PRB'', ''2026-01-01'');
    INSERT dbo.empleado (nombre, apellidos, puesto, cedula_profesional, fecha_ingreso) VALUES (N''Vet'', N''Dos'', N''Veterinario'', N''CED-PRB'', ''2026-01-01'');', N'2601';

/* RD-07: el disparador rechaza la modificación y la transacción de la aplicación sigue utilizable (D-13) */
EXEC #probar_rechazo N'RD-07 · Modificar un movimiento de inventario', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Admin'', N''Administrador'', ''2026-01-01'');
    DECLARE @e INT = SCOPE_IDENTITY();
    INSERT dbo.producto (codigo, nombre, categoria, unidad_medida, precio_venta) VALUES (N''PRB-3'', N''Prueba'', N''Insumo'', N''Pieza'', 10);
    INSERT dbo.lote (id_producto, numero_lote, cantidad_disponible) VALUES (SCOPE_IDENTITY(), N''L1'', 5);
    INSERT dbo.movimiento_inventario (id_lote, id_empleado, tipo, cantidad) VALUES (SCOPE_IDENTITY(), @e, N''Entrada'', 5);
    UPDATE dbo.movimiento_inventario SET cantidad = 50 WHERE id_movimiento = SCOPE_IDENTITY();', N'50000', 1;

EXEC #probar_rechazo N'RD-07 · Borrar un movimiento de inventario', N'
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N''Prueba'', N''Admin'', N''Administrador'', ''2026-01-01'');
    DECLARE @e INT = SCOPE_IDENTITY();
    INSERT dbo.producto (codigo, nombre, categoria, unidad_medida, precio_venta) VALUES (N''PRB-4'', N''Prueba'', N''Insumo'', N''Pieza'', 10);
    INSERT dbo.lote (id_producto, numero_lote, cantidad_disponible) VALUES (SCOPE_IDENTITY(), N''L1'', 5);
    INSERT dbo.movimiento_inventario (id_lote, id_empleado, tipo, cantidad) VALUES (SCOPE_IDENTITY(), @e, N''Entrada'', 5);
    DELETE dbo.movimiento_inventario WHERE id_movimiento = SCOPE_IDENTITY();', N'50000', 1;
GO

/* ---------- 3. Lo que la base debe ACEPTAR ---------- */
DECLARE @det NVARCHAR(600), @res NVARCHAR(10) = N'FALLA';
BEGIN TRANSACTION;
BEGIN TRY
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N'Uno', N'Sin cédula', N'Estilista', '2026-01-01');
    INSERT dbo.empleado (nombre, apellidos, puesto, fecha_ingreso) VALUES (N'Dos', N'Sin cédula', N'Recepcionista', '2026-01-01');
    SELECT @res = N'PASA', @det = N'Se aceptaron dos empleados sin cédula';
END TRY
BEGIN CATCH
    SET @det = CONCAT(N'Error ', ERROR_NUMBER(), N': ', ERROR_MESSAGE());
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
INSERT #resultados (prueba, resultado, detalle) VALUES (N'D-12 · Varios empleados sin cédula (índice filtrado)', @res, @det);
GO

DECLARE @stock INT, @bajo BIT, @caduca BIT, @det NVARCHAR(600), @res NVARCHAR(10) = N'FALLA';
BEGIN TRANSACTION;
BEGIN TRY
    INSERT dbo.producto (codigo, nombre, categoria, unidad_medida, precio_venta, stock_minimo)
    VALUES (N'PRB-5', N'Vacuna de prueba', N'Vacuna', N'Dosis', 100, 10);
    DECLARE @p INT = SCOPE_IDENTITY();
    INSERT dbo.lote (id_producto, numero_lote, fecha_caducidad, cantidad_disponible) VALUES
        (@p, N'VIGENTE', DATEADD(DAY, 20, CAST(GETDATE() AS DATE)), 6),
        (@p, N'VENCIDO', DATEADD(DAY, -1, CAST(GETDATE() AS DATE)), 50);
    SELECT @stock = stock_disponible, @bajo = bajo_minimo, @caduca = caduca_en_30_dias
    FROM dbo.vista_stock_disponible WHERE id_producto = @p;
    IF @stock = 6 AND @bajo = 1 AND @caduca = 1 SET @res = N'PASA';
    SET @det = CONCAT(N'stock = ', @stock, N' (esperado 6, el lote vencido no cuenta) · bajo mínimo = ', @bajo,
                      N' · caduca en 30 días = ', @caduca);
END TRY
BEGIN CATCH
    SET @det = CONCAT(N'Error ', ERROR_NUMBER(), N': ', ERROR_MESSAGE());
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
INSERT #resultados (prueba, resultado, detalle) VALUES (N'RD-03, RD-05, RF-11 · Vista de stock disponible', @res, @det);
GO

/* ---------- Resultado ---------- */
SELECT n AS [#], prueba AS [Prueba], resultado AS [Resultado], detalle AS [Detalle] FROM #resultados ORDER BY n;

SELECT COUNT(*) AS [Pruebas],
       SUM(CASE WHEN resultado = N'PASA' THEN 1 ELSE 0 END) AS [Pasan],
       SUM(CASE WHEN resultado = N'FALLA' THEN 1 ELSE 0 END) AS [Fallan],
       (SELECT COUNT(*) FROM dbo.cliente) AS [Clientes en la base (debe seguir igual)]
FROM #resultados;
GO
