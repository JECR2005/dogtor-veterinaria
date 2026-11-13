/* =============================================================================
   Dogtor: Veterinaria & Petcare · Sistema de gestión
   00 · Crea la base de datos y la cuenta de la aplicación (SQL Server 2016 o posterior)

   Ejecutar UNA VEZ conectado a «master» con una cuenta administradora
   (sa o una cuenta de Windows con rol sysadmin), en SSMS o con:
       sqlcmd -S localhost\SQLEXPRESS -E -C -i bd\00_crear_base_y_usuario.sql

   Antes de ejecutar: cambie la contraseña de dogtor_app (línea marcada) y póngala
   también en DB_CONTRASENA del archivo .env.
   Si va a usar autenticación de Windows (DB_USUARIO vacío en .env), basta con
   crear la base (primer bloque); los demás bloques son para la cuenta SQL.
   ============================================================================= */

-- 1. Base de datos. Intercalación en español: sin distinguir mayúsculas, sí acentos.
IF DB_ID(N'Dogtor') IS NULL
    CREATE DATABASE Dogtor COLLATE Modern_Spanish_CI_AS;
GO

-- 2. Cuenta de la aplicación (requiere autenticación mixta en la instancia).
IF SUSER_ID(N'dogtor_app') IS NULL
    CREATE LOGIN dogtor_app
        WITH PASSWORD = N'Cambiar-Esta-Contrasena-2026',   -- <<< CAMBIAR
             DEFAULT_DATABASE = Dogtor,
             CHECK_POLICY = ON;
GO

-- 3. SOLO EN DESARROLLO: permite que pytest cree su base de pruebas (test_Dogtor) y que
--    scripts/respaldo.py pruebe restauraciones. En producción NO se ejecuta este bloque.
ALTER SERVER ROLE dbcreator ADD MEMBER dogtor_app;
GO

-- 4. Usuario dentro de la base. db_owner porque Django crea sus propias tablas
--    (sesiones, tipos de contenido, historial de migraciones) en la misma base.
USE Dogtor;
GO
IF USER_ID(N'dogtor_app') IS NULL
    CREATE USER dogtor_app FOR LOGIN dogtor_app;
GO
ALTER ROLE db_owner ADD MEMBER dogtor_app;
GO

PRINT N'Base Dogtor y cuenta dogtor_app listas. Siguiente paso: bd\01_tablas.sql';
GO
