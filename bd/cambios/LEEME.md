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

## Cómo aplicar un cambio

Desde la raíz del proyecto, con el entorno virtual activo (usa la conexión de `.env`):

    python bd/ejecutar.py --cambio bd/cambios/AAAA-MM-DD_<requisito>_<tema>.sql

o abrir el script en SSMS con la base Dogtor seleccionada y pulsar Ejecutar. Los scripts de esta carpeta se pueden
ejecutar más de una vez. Anotar cada ejecución en `docs/gestion/registro_ejecucion_bd.md`.

## Cambios

| Fecha | Script | Qué cambia | Decisión |
|---|---|---|---|
| 2026-11-17 | `2026-11-17_RD-05_cantidad_decimal.sql` | `lote.cantidad_disponible` y `movimiento_inventario.cantidad` de INT a DECIMAL(10,2) | D-04 |
