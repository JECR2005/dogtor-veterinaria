# Registro de pruebas de restauración (RNF-04, TS-07)

Meta: restaurar un respaldo en menos de 120 minutos, una vez por prototipo.
Herramientas: `python scripts/respaldo.py probar --prototipo Pn` o `bd/04_prueba_respaldo.sql` en SSMS.

| Fecha | Prototipo | Respaldo | Tamaño | Respaldo (s) | Restauración (s) | Tablas restauradas | Resultado | Ejecutó |
|---|---|---|---|---|---|---|---|---|
| 2026-11-13 16:26 | S0 | `C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\Backup\Dogtor_2026-11-13_1626.bak` (con CHECKSUM, VERIFYONLY correcto) | 6.71 MB | 0.22 | 0.52 | 26 de 26 + 1 vista | Cumple | Claude, en SSMS 21 (MSI\SQLEXPRESS) |
| 2026-11-17 18:12 | P1 | `C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\Dogtor_2026-11-17_*.bak` (con CHECKSUM, VERIFYONLY correcto) | 7.15 MB | 0.14 | 0.60 | 33 de 33 (26 del sistema + 7 de Django) + 1 vista | Cumple | JECR2005, en SSMS con `bd/04_prueba_respaldo.sql` (SQL Server 2025, `localhost`, laptop nueva: servidor limpio, LV-03 punto 19) |
| 2026-11-18 19:55 | P2 | `C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\Dogtor_2026-11-18_*.bak` (con CHECKSUM, VERIFYONLY correcto) | 7.65 MB | 0.16 | 0.56 | 33 de 33 (26 del sistema + 7 de Django) + 1 vista | Cumple | JECR2005, en SSMS con `bd/04_prueba_respaldo.sql` (SQL Server 2025, `localhost`), con los datos de P2 |
| 2026-11-20 09:18 | P3 | `C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\Dogtor_2026-11-20_*.bak` (con CHECKSUM, VERIFYONLY correcto) | 10.09 MB | 0.19 | 1.84 | 33 de 33 (26 del sistema + 7 de Django) + 1 vista | Cumple | JECR2005, en SSMS con `bd/04_prueba_respaldo.sql` (SQL Server 2025, `localhost`), con los datos de P3 después de la aceptación |
| 2026-11-20 14:20 | P4 | `C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\Dogtor_2026-11-20_*.bak` (con CHECKSUM, VERIFYONLY correcto) | 11.09 MB | 0.18 | 0.62 | 33 de 33 (26 del sistema + 7 de Django) + 1 vista | Cumple | JECR2005, en SSMS con `bd/04_prueba_respaldo.sql` (SQL Server 2025, `localhost`), con los datos de P4 después de la aceptación |
| 2026-11-21 11:20 | P5 | `C:\DogtorRespaldos\Dogtor_2026-11-21_112014.bak` (con CHECKSUM, VERIFYONLY correcto) restaurado en un **servidor limpio**: SQL Server 2025 en Docker (TS-07, D-24) | 12.12 MB | 0.34 | 1.02 | 33 de 33, con los mismos registros (4,498) y DBCC CHECKDB sin errores (`ts07_restauracion.md`) | Cumple | JECR2005, con `python scripts/respaldo.py ts07` |
