/* =============================================================================
   Dogtor: Veterinaria & Petcare · Cambio al esquema (S4-16, decisión D-21)
   2026-11-20 · RD-06, RD-11 y RD-12 · La base protege las ventas

   Qué cambia:
     Función dbo.fn_linea_con_receta_valida y CHECK CK_detalle_venta_receta_valida: un medicamento que
         requiere receta solo entra al ticket con una receta que lo incluye (RD-12)
     Disparador TR_detalle_venta_precio_historico: las líneas no se modifican (RD-11)
     Disparador TR_pago_inmutable: los pagos no se modifican ni se borran (RD-06, RD-07)
     Disparador TR_venta_cancelada_solo_lectura: un ticket cancelado queda en solo lectura (RF-14)
   Por qué: el servicio ya lo valida, pero un QuerySet.update(), un create() directo o SQL se lo saltaba.

   Para una base que YA existe. Las bases nuevas ya nacen así (bd/01_tablas.sql). Se puede ejecutar más de
   una vez. La restricción se agrega WITH NOCHECK: las líneas que ya existen no se vuelven a revisar.

   Ejecutar conectado a la base Dogtor:
       python bd/ejecutar.py --cambio bd/cambios/2026-11-20_RD-06_RD-11_RD-12_ventas.sql
   o abrirlo en SSMS con la base Dogtor seleccionada y pulsar Ejecutar.

   Todo va en UN solo lote (sin GO dentro de la transacción) por MARS (error 3997); la función, la
   restricción y los disparadores van en EXEC porque deben ser la primera instrucción de su lote.
   ============================================================================= */
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.fn_linea_con_receta_valida', N'FN') IS NULL
        EXEC (N'CREATE FUNCTION dbo.fn_linea_con_receta_valida (@id_producto INT, @id_receta INT)
RETURNS BIT
AS
BEGIN
    -- RD-12: 1 si la línea es un servicio, si el producto no requiere receta, o si la receta lo incluye
    IF @id_producto IS NULL
        RETURN 1;
    IF NOT EXISTS (SELECT 1 FROM dbo.producto WHERE id_producto = @id_producto AND requiere_receta = 1)
        RETURN 1;
    IF @id_receta IS NOT NULL
       AND EXISTS (SELECT 1 FROM dbo.detalle_receta WHERE id_receta = @id_receta AND id_producto = @id_producto)
        RETURN 1;
    RETURN 0;
END;');

    IF OBJECT_ID(N'dbo.CK_detalle_venta_receta_valida', N'C') IS NULL
        EXEC (N'ALTER TABLE dbo.detalle_venta WITH NOCHECK ADD CONSTRAINT CK_detalle_venta_receta_valida CHECK (dbo.fn_linea_con_receta_valida(id_producto, id_receta) = 1);');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_detalle_venta_precio_historico
ON dbo.detalle_venta
INSTEAD OF UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    -- RD-11: la línea conserva el precio, la cantidad y el importe con que se generó el ticket. No se usa
    -- INSTEAD OF DELETE porque las líneas se borran en cascada con su venta (y una venta no se borra).
    SET XACT_ABORT OFF;
    RAISERROR (N''RD-11: las líneas del ticket conservan el precio con que se generaron; no se modifican.'', 16, 1);
    RETURN;
END;');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_pago_inmutable
ON dbo.pago
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    -- RD-06 y RD-07: un pago no se modifica ni se borra; lo que se devuelve se registra como «Devolución».
    SET XACT_ABORT OFF;
    RAISERROR (N''RD-07: los pagos no se modifican ni se borran; registre una devolución.'', 16, 1);
    RETURN;
END;');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_venta_cancelada_solo_lectura
ON dbo.venta
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM deleted WHERE estado = N''Cancelada'')
        RETURN;  -- ticket vigente (o su cancelación): se guarda normal
    -- RF-14: un ticket cancelado queda en solo lectura; se regresan sus valores y se avisa
    SET XACT_ABORT OFF;
    UPDATE v
       SET folio_ticket = d.folio_ticket, id_cliente = d.id_cliente, id_empleado = d.id_empleado,
           id_cita = d.id_cita, fecha_hora = d.fecha_hora, total = d.total, saldo = d.saldo,
           estado = d.estado, requiere_factura = d.requiere_factura,
           motivo_cancelacion = d.motivo_cancelacion, id_cancelo = d.id_cancelo
      FROM dbo.venta AS v
      JOIN deleted AS d ON d.id_venta = v.id_venta
     WHERE d.estado = N''Cancelada'';
    RAISERROR (N''RF-14: el ticket está cancelado y es de solo lectura.'', 16, 1);
END;');

    COMMIT TRANSACTION;
    SET XACT_ABORT OFF;
    PRINT N'Cambio 2026-11-20_RD-06_RD-11_RD-12_ventas aplicado: la base protege las ventas.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET XACT_ABORT OFF;
    THROW;
END CATCH;
GO
