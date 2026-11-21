/* =============================================================================
   Dogtor: Veterinaria & Petcare · Cambio al esquema (S5-04, decisión D-23)
   2026-11-21 · RNF-03 · La bitácora no se modifica ni se borra

   Qué cambia:
     Disparador TR_bitacora_inmutable: los registros de la bitácora no se modifican ni se borran
     Índice IX_bitacora_usuario_fecha: la consulta de UI-20 por usuario y fecha
   Por qué: desde P5 la bitácora guarda los cambios de ventas, consultas, recetas e inventario con sus valores
   previos; es evidencia y nadie debe poder alterarla, ni con un QuerySet.update(), ni con SQL.

   Para una base que YA existe. Las bases nuevas ya nacen así (bd/01_tablas.sql). Se puede ejecutar más de
   una vez.

   Ejecutar conectado a la base Dogtor:
       python bd/ejecutar.py --cambio bd/cambios/2026-11-21_RNF-03_bitacora_inmutable.sql
   o abrirlo en SSMS con la base Dogtor seleccionada y pulsar Ejecutar.

   Todo va en UN solo lote (sin GO dentro de la transacción) por MARS (error 3997); el disparador va en EXEC
   porque debe ser la primera instrucción de su lote.
   ============================================================================= */
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    IF INDEXPROPERTY(OBJECT_ID(N'dbo.bitacora_auditoria'), N'IX_bitacora_usuario_fecha', N'IndexID') IS NULL
        EXEC (N'CREATE INDEX IX_bitacora_usuario_fecha ON dbo.bitacora_auditoria (id_usuario, fecha_hora);');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_bitacora_inmutable
ON dbo.bitacora_auditoria
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    -- RNF-03: lo registrado en la bitácora es evidencia; no cambia ni se borra desde la aplicación ni con SQL
    SET XACT_ABORT OFF;
    RAISERROR (N''RNF-03: la bitácora no se modifica ni se borra.'', 16, 1);
    RETURN;
END;');

    COMMIT TRANSACTION;
    SET XACT_ABORT OFF;
    PRINT N'Cambio 2026-11-21_RNF-03_bitacora_inmutable aplicado: la bitácora no se modifica ni se borra.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET XACT_ABORT OFF;
    THROW;
END CATCH;
GO
