/* =============================================================================
   Dogtor · 04 · Respaldo y prueba de restauración en SSMS (RNF-04, TS-07, riesgo R05)
   Equivalente en T-SQL de `python scripts/respaldo.py respaldar` + `probar`, para usarlo sin Python.

   Ejecutar conectado a «master» con una cuenta que pueda respaldar y crear bases (sysadmin o
   db_owner de Dogtor + dbcreator). Pasos:
     1. BACKUP DATABASE Dogtor en la carpeta de respaldos de la instancia, con CHECKSUM.
     2. RESTORE VERIFYONLY: comprueba que el archivo .bak es legible y está íntegro.
     3. RESTORE en la base temporal Dogtor_prueba_restauracion, midiendo el tiempo (meta < 120 min).
     4. Cuenta las tablas y la vista restauradas y compara con la base original.
     5. Borra SOLO la base temporal. El archivo .bak se conserva como respaldo.
   La copia externa y la retención de 30 días las hace scripts/respaldo.py (o el Programador de tareas).
   ============================================================================= */

USE master;
SET NOCOUNT ON;

DECLARE @base_origen  SYSNAME = N'Dogtor',
        @base_prueba  SYSNAME = N'Dogtor_prueba_restauracion',
        @carpeta      NVARCHAR(400) = CAST(SERVERPROPERTY('InstanceDefaultBackupPath') AS NVARCHAR(400)),
        @datos        NVARCHAR(400) = CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS NVARCHAR(400)),
        @registro     NVARCHAR(400) = CAST(SERVERPROPERTY('InstanceDefaultLogPath') AS NVARCHAR(400)),
        @archivo      NVARCHAR(600), @sql NVARCHAR(MAX), @move NVARCHAR(MAX) = N'',
        @t0 DATETIME2, @t1 DATETIME2, @t2 DATETIME2, @t3 DATETIME2,
        @tablas_origen INT, @tablas_prueba INT, @vistas_prueba INT, @tamano_mb DECIMAL(10,2);

IF DB_ID(@base_origen) IS NULL
    THROW 50000, N'No existe la base Dogtor.', 1;
IF RIGHT(@carpeta, 1) <> N'\' SET @carpeta += N'\';
SET @archivo = CONCAT(@carpeta, @base_origen, N'_', FORMAT(SYSDATETIME(), 'yyyy-MM-dd_HHmm'), N'.bak');

-- 1. Respaldo completo con suma de verificación
SET @t0 = SYSDATETIME();
BACKUP DATABASE @base_origen TO DISK = @archivo
    WITH INIT, CHECKSUM, NAME = N'Respaldo completo de Dogtor (RNF-04)';
SET @t1 = SYSDATETIME();

-- 2. Verificación de integridad del archivo
RESTORE VERIFYONLY FROM DISK = @archivo WITH CHECKSUM;

-- 3. Restauración en una base temporal (los archivos van a las carpetas por defecto de la instancia)
IF DB_ID(@base_prueba) IS NOT NULL
BEGIN
    SET @sql = CONCAT(N'ALTER DATABASE ', QUOTENAME(@base_prueba), N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE ',
                      QUOTENAME(@base_prueba), N';');
    EXEC (@sql);
END;

-- Las rutas se citan con REPLACE (QUOTENAME solo admite 128 caracteres y una ruta puede ser más larga)
SELECT @move += CONCAT(N', MOVE N''', REPLACE(name, N'''', N''''''), N''' TO N''',
                       REPLACE(CONCAT(CASE WHEN type = 1 THEN @registro ELSE @datos END,
                                      @base_prueba, N'_', name, CASE WHEN type = 1 THEN N'.ldf' ELSE N'.mdf' END),
                               N'''', N''''''), N'''')
FROM sys.master_files WHERE database_id = DB_ID(@base_origen);

SET @sql = CONCAT(N'RESTORE DATABASE ', QUOTENAME(@base_prueba), N' FROM DISK = N''', REPLACE(@archivo, N'''', N''''''),
                  N''' WITH RECOVERY', @move, N';');
SET @t2 = SYSDATETIME();
EXEC (@sql);
SET @t3 = SYSDATETIME();

-- 4. Comparación de objetos restaurados
SET @sql = CONCAT(N'SELECT @t = COUNT(*) FROM ', QUOTENAME(@base_prueba), N'.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = ''BASE TABLE'';',
                  N'SELECT @v = COUNT(*) FROM ', QUOTENAME(@base_prueba), N'.INFORMATION_SCHEMA.VIEWS;');
EXEC sp_executesql @sql, N'@t INT OUTPUT, @v INT OUTPUT', @t = @tablas_prueba OUTPUT, @v = @vistas_prueba OUTPUT;
SET @sql = CONCAT(N'SELECT @t = COUNT(*) FROM ', QUOTENAME(@base_origen), N'.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = ''BASE TABLE'';');
EXEC sp_executesql @sql, N'@t INT OUTPUT', @t = @tablas_origen OUTPUT;

SELECT TOP (1) @tamano_mb = CAST(backup_size / 1048576.0 AS DECIMAL(10,2))
FROM msdb.dbo.backupset WHERE database_name = @base_origen ORDER BY backup_finish_date DESC;

-- 5. Se borra solo la base temporal
SET @sql = CONCAT(N'ALTER DATABASE ', QUOTENAME(@base_prueba), N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE ',
                  QUOTENAME(@base_prueba), N';');
EXEC (@sql);

-- Resultado (TS-07)
SELECT
    @archivo                                                  AS [Archivo de respaldo],
    @tamano_mb                                                AS [Tamaño (MB)],
    CAST(DATEDIFF(MILLISECOND, @t0, @t1) / 1000.0 AS DECIMAL(10,2)) AS [Respaldo (s)],
    CAST(DATEDIFF(MILLISECOND, @t2, @t3) / 1000.0 AS DECIMAL(10,2)) AS [Restauración (s)],
    CONCAT(@tablas_prueba, N' de ', @tablas_origen)           AS [Tablas restauradas],
    @vistas_prueba                                            AS [Vistas restauradas],
    CASE WHEN DATEDIFF(SECOND, @t2, @t3) < 7200 AND @tablas_prueba = @tablas_origen
         THEN N'CUMPLE (meta < 120 min)' ELSE N'NO CUMPLE' END AS [Resultado RNF-04],
    CASE WHEN DB_ID(@base_prueba) IS NULL THEN N'Base temporal borrada' ELSE N'Revisar: base temporal sigue' END AS [Limpieza];
