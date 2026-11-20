# Registro de ejecución de los scripts de base de datos

| Fecha | Servidor | Base | Scripts | Resultado | Ejecutó |
|---|---|---|---|---|---|
| 2026-11-13 15:55 | MSI\\SQLEXPRESS · SQL Server 2022 Express 16.0.1210 · autenticación de Windows | Dogtor (Modern_Spanish_CI_AS) | 00 (solo creación de la base), 01_tablas, 02_vistas, 03_prueba_esquema | 26 tablas · 26 PK · 41 FK · 12 UQ · 60 CHECK · 35 DEFAULT · vista y disparador creados · **19/19 pruebas PASA**, sin datos residuales | Claude, en SSMS 21 del equipo de Jesús Enrique |
| 2026-11-17 19:30 | localhost (instancia predeterminada) · SQL Server 2025 · autenticación de Windows | Dogtor | `bd/cambios/2026-11-17_RD-05_cantidad_decimal.sql` con `bd/ejecutar.py --cambio`; después `bd/ejecutar.py --recrear` (99, 01, 02 y migrate) y `cargar_datos_prueba` | Columnas `decimal(10,2)` comprobadas en SSMS; migración `inventario.0002` aplicada; vista con las alertas esperadas (VAC-003 y ALI-002 bajo mínimo, VAC-001 y MED-001 por caducar, MED-003 en 97.50) y 3 pedidos. Antes de las correcciones: DEF-005 y DEF-006 | JECR2005, en la laptop nueva |
| 2026-11-19 18:15 | localhost (instancia predeterminada) · SQL Server 2025 · autenticación de Windows | Dogtor (con los datos ficticios de P3) | `bd/cambios/2026-11-19_RD-07_RD-08_consulta_firmada.sql` con `bd/ejecutar.py --cambio`, dos veces seguidas | «✓» y «Esquema listo.» las dos veces: el cambio se aplica y se puede repetir. El primer intento (18:00) se revirtió sin cambios por DEF-007 | JECR2005, en la laptop nueva |
| 2026-11-20 14:00 | localhost (instancia predeterminada) · SQL Server 2025 · autenticación de Windows | Dogtor (con los datos ficticios de P4) | `bd/cambios/2026-11-20_RD-06_RD-11_RD-12_ventas.sql` con `bd/ejecutar.py --cambio`, dos veces seguidas | «✓» y «Esquema listo.» las dos veces: el cambio D-21 se aplica y se puede repetir | JECR2005, en la laptop nueva |

Notas:
- No se creó la cuenta SQL `dogtor_app` (bloques 2 a 4 del script 00): el equipo usa autenticación de Windows.
  En `.env`: `DB_HOST=MSI\SQLEXPRESS` y `DB_USUARIO=` vacío.
