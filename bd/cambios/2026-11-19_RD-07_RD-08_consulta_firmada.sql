/* =============================================================================
   Dogtor: Veterinaria & Petcare · Cambio al esquema (S3-15)
   2026-11-19 · RD-07 y RD-08 · La base protege la consulta firmada

   Qué cambia:
     Funciones dbo.fn_consulta_abierta y dbo.fn_receta_en_consulta_abierta
     CHECK CK_aplicacion_consulta_abierta, CK_receta_consulta_abierta, CK_detalle_receta_consulta_abierta:
         solo se agregan aplicaciones y recetas a una consulta Abierta (RD-07, RD-08)
     Disparadores TR_consulta_firmada_solo_lectura, TR_consulta_firmada_no_se_borra y
         TR_aplicacion_de_consulta_firmada: una consulta firmada no cambia, no se borra ni pierde aplicaciones
   Por qué: el servicio ya lo valida (TU-14, TU-15), pero una actualización directa (QuerySet.update o SQL)
   se lo saltaba. Igual que RD-05 en S2-13, la base vuelve a exigir la regla.

   Para una base que YA existe. Las bases nuevas ya nacen así (bd/01_tablas.sql). Se puede ejecutar más de
   una vez: lo que ya existe no se vuelve a crear y los disparadores se reemplazan.

   Ejecutar conectado a la base Dogtor:
       python bd/ejecutar.py --cambio bd/cambios/2026-11-19_RD-07_RD-08_consulta_firmada.sql
   o abrirlo en SSMS con la base Dogtor seleccionada y pulsar Ejecutar.

   Las restricciones se agregan WITH NOCHECK: las aplicaciones y recetas que ya existen en consultas firmadas
   se capturaron cuando la consulta estaba abierta y son válidas; la regla se exige a partir de ahora.

   Todo va en UN solo lote (sin GO dentro de la transacción) por MARS (error 3997); las funciones, las
   restricciones y los disparadores van en EXEC porque CREATE FUNCTION y CREATE TRIGGER deben ser la primera
   instrucción de su lote.
   ============================================================================= */
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.fn_consulta_abierta', N'FN') IS NULL
        EXEC (N'CREATE FUNCTION dbo.fn_consulta_abierta (@id_consulta INT)
RETURNS BIT
AS
BEGIN
    -- RD-07 y RD-08: 1 si la consulta existe y sigue Abierta
    RETURN CASE WHEN EXISTS (SELECT 1 FROM dbo.consulta WHERE id_consulta = @id_consulta AND estado = N''Abierta'')
                THEN 1 ELSE 0 END;
END;');

    IF OBJECT_ID(N'dbo.fn_receta_en_consulta_abierta', N'FN') IS NULL
        EXEC (N'CREATE FUNCTION dbo.fn_receta_en_consulta_abierta (@id_receta INT)
RETURNS BIT
AS
BEGIN
    RETURN (SELECT dbo.fn_consulta_abierta(id_consulta) FROM dbo.receta WHERE id_receta = @id_receta);
END;');

    IF OBJECT_ID(N'dbo.CK_aplicacion_consulta_abierta', N'C') IS NULL
        EXEC (N'ALTER TABLE dbo.aplicacion WITH NOCHECK ADD CONSTRAINT CK_aplicacion_consulta_abierta CHECK (dbo.fn_consulta_abierta(id_consulta) = 1);');

    IF OBJECT_ID(N'dbo.CK_receta_consulta_abierta', N'C') IS NULL
        EXEC (N'ALTER TABLE dbo.receta WITH NOCHECK ADD CONSTRAINT CK_receta_consulta_abierta CHECK (dbo.fn_consulta_abierta(id_consulta) = 1);');

    IF OBJECT_ID(N'dbo.CK_detalle_receta_consulta_abierta', N'C') IS NULL
        EXEC (N'ALTER TABLE dbo.detalle_receta WITH NOCHECK ADD CONSTRAINT CK_detalle_receta_consulta_abierta CHECK (dbo.fn_receta_en_consulta_abierta(id_receta) = 1);');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_consulta_firmada_solo_lectura
ON dbo.consulta
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM deleted WHERE estado = N''Firmada'')
        RETURN;  -- consulta Abierta (o su firma): se guarda normal
    IF CAST(SESSION_CONTEXT(N''correccion_autorizada'') AS INT) = 1
        RETURN;  -- P5: corrección del Administrador que queda en la bitácora (RNF-03)
    -- Una firmada no cambia: se regresan sus valores y se avisa sin anular la transacción de la aplicación
    -- (XACT_ABORT OFF y RAISERROR, igual que TR_movimiento_inventario_inmutable).
    SET XACT_ABORT OFF;
    UPDATE c
       SET id_expediente = d.id_expediente, id_cita = d.id_cita, id_empleado = d.id_empleado,
           fecha_hora = d.fecha_hora, sintomas = d.sintomas, peso_kg = d.peso_kg,
           temperatura_c = d.temperatura_c, diagnostico = d.diagnostico, tratamiento = d.tratamiento,
           observaciones = d.observaciones, estado = d.estado, fecha_firma = d.fecha_firma
      FROM dbo.consulta AS c
      JOIN deleted AS d ON d.id_consulta = c.id_consulta
     WHERE d.estado = N''Firmada'';
    RAISERROR (N''RD-07: la consulta está firmada y es de solo lectura.'', 16, 1);
END;');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_consulta_firmada_no_se_borra
ON dbo.consulta
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted WHERE estado = N''Firmada'')
    BEGIN
        SET XACT_ABORT OFF;
        RAISERROR (N''RD-07: una consulta firmada no se borra.'', 16, 1);
        RETURN;
    END;
    DELETE c FROM dbo.consulta AS c JOIN deleted AS d ON d.id_consulta = c.id_consulta;
END;');

    EXEC (N'CREATE OR ALTER TRIGGER dbo.TR_aplicacion_de_consulta_firmada
ON dbo.aplicacion
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted AS d JOIN dbo.consulta AS c ON c.id_consulta = d.id_consulta
               WHERE c.estado = N''Firmada'')
    BEGIN
        SET XACT_ABORT OFF;
        RAISERROR (N''RD-07: la aplicación pertenece a una consulta firmada y no se quita.'', 16, 1);
        RETURN;
    END;
    DELETE a FROM dbo.aplicacion AS a JOIN deleted AS d ON d.id_aplicacion = a.id_aplicacion;
END;');

    COMMIT TRANSACTION;
    SET XACT_ABORT OFF;
    PRINT N'Cambio 2026-11-19_RD-07_RD-08_consulta_firmada aplicado: la base protege la consulta firmada.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET XACT_ABORT OFF;
    THROW;
END CATCH;
GO
