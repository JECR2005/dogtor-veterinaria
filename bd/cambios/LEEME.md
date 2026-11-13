# Cambios al esquema

`bd/01_tablas.sql` siempre describe el esquema **completo y vigente**: con él se crean las bases nuevas y la
base de las pruebas. Cuando una base ya existe (la de cada integrante o la del local), los cambios se
aplican con un script incremental guardado aquí.

Por cada cambio, en el mismo pull request:

1. Script incremental: `bd/cambios/AAAA-MM-DD_<requisito>_<tema>.sql` (por ejemplo
   `2026-11-24_RD-05_cantidad_decimal.sql`), que se pueda ejecutar una sola vez sobre una base existente.
2. El mismo cambio reflejado en `bd/01_tablas.sql` (o `02_vistas.sql`).
3. El modelo de Django ajustado y su migración (`makemigrations`; con `managed = False` no crea tablas).
4. El diccionario de datos (apartado 3.5) actualizado y, si aplica, una entrada en `docs/decisiones.md`.
