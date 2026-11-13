# Registro de ejecución de los scripts de base de datos

| Fecha | Servidor | Base | Scripts | Resultado | Ejecutó |
|---|---|---|---|---|---|
| 2026-11-13 15:55 | MSI\\SQLEXPRESS · SQL Server 2022 Express 16.0.1210 · autenticación de Windows | Dogtor (Modern_Spanish_CI_AS) | 00 (solo creación de la base), 01_tablas, 02_vistas, 03_prueba_esquema | 26 tablas · 26 PK · 41 FK · 12 UQ · 60 CHECK · 35 DEFAULT · vista y disparador creados · **19/19 pruebas PASA**, sin datos residuales | Claude, en SSMS 21 del equipo de Jesús Enrique |

Notas:
- No se creó la cuenta SQL `dogtor_app` (bloques 2 a 4 del script 00): el equipo usa autenticación de Windows.
  En `.env`: `DB_HOST=MSI\SQLEXPRESS` y `DB_USUARIO=` vacío.
