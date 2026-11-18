# Registro de pruebas de restauración (RNF-04, TS-07)

Meta: restaurar un respaldo en menos de 120 minutos, una vez por prototipo.
Herramientas: `python scripts/respaldo.py probar --prototipo Pn` o `bd/04_prueba_respaldo.sql` en SSMS.

| Fecha | Prototipo | Respaldo | Tamaño | Respaldo (s) | Restauración (s) | Tablas restauradas | Resultado | Ejecutó |
|---|---|---|---|---|---|---|---|---|
| 2026-11-13 16:26 | S0 | `C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\Backup\Dogtor_2026-11-13_1626.bak` (con CHECKSUM, VERIFYONLY correcto) | 6.71 MB | 0.22 | 0.52 | 26 de 26 + 1 vista | Cumple | Claude, en SSMS 21 (MSI\SQLEXPRESS) |
| 2026-11-17 18:12 | P1 | `C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\Dogtor_2026-11-17_*.bak` (con CHECKSUM, VERIFYONLY correcto) | 7.15 MB | 0.14 | 0.60 | 33 de 33 (26 del sistema + 7 de Django) + 1 vista | Cumple | JECR2005, en SSMS con `bd/04_prueba_respaldo.sql` (SQL Server 2025, `localhost`, laptop nueva: servidor limpio, LV-03 punto 19) |
