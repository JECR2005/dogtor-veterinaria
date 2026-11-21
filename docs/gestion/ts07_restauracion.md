# TS-07 · Restauración en un servidor limpio (RNF-04)

Generado por `python scripts/respaldo.py ts07` (S5-09, D-24). Criterio de la Tabla 4.15: restauración en menos de 120 minutos y datos íntegros.

| Dato | Valor |
|---|---|
| Fecha | 2026-11-21 11:20 |
| Base de origen | `Dogtor` en `localhost` |
| Servidor limpio | `localhost,14330` · SQL Server 17.0.5065.9 (Enterprise Developer Edition (64-bit)) |
| Respaldo | `Dogtor_2026-11-21_112014.bak` · 12.12 MB · 0.34 s |
| Restauración | 1.02 s (0.02 min) |
| Integridad (DBCC CHECKDB) | Sin errores |
| Tablas | 33 · 33 con el mismo número de registros |
| Registros | 4,498 en el origen · 4,498 restaurados |
| Resultado | **Cumple** |
| Ejecutó | jesus |

| Tabla | Origen | Restaurada | Igual |
|---|---:|---:|:---:|
| `dbo.aplicacion` | 4 | 4 | Sí |
| `dbo.auth_group` | 0 | 0 | Sí |
| `dbo.auth_group_permissions` | 0 | 0 | Sí |
| `dbo.auth_permission` | 124 | 124 | Sí |
| `dbo.bitacora_auditoria` | 4 | 4 | Sí |
| `dbo.cita` | 215 | 215 | Sí |
| `dbo.cliente` | 710 | 710 | Sí |
| `dbo.consulta` | 212 | 212 | Sí |
| `dbo.detalle_pedido` | 4 | 4 | Sí |
| `dbo.detalle_receta` | 0 | 0 | Sí |
| `dbo.detalle_venta` | 214 | 214 | Sí |
| `dbo.django_admin_log` | 0 | 0 | Sí |
| `dbo.django_content_type` | 31 | 31 | Sí |
| `dbo.django_migrations` | 26 | 26 | Sí |
| `dbo.django_session` | 3 | 3 | Sí |
| `dbo.empleado` | 4 | 4 | Sí |
| `dbo.especie` | 2 | 2 | Sí |
| `dbo.expediente_clinico` | 1200 | 1200 | Sí |
| `dbo.horario_laboral` | 24 | 24 | Sí |
| `dbo.lote` | 18 | 18 | Sí |
| `dbo.mascota` | 1200 | 1200 | Sí |
| `dbo.movimiento_inventario` | 30 | 30 | Sí |
| `dbo.pago` | 214 | 214 | Sí |
| `dbo.pedido_compra` | 3 | 3 | Sí |
| `dbo.producto` | 11 | 11 | Sí |
| `dbo.proveedor` | 3 | 3 | Sí |
| `dbo.raza` | 15 | 15 | Sí |
| `dbo.receta` | 0 | 0 | Sí |
| `dbo.recordatorio` | 3 | 3 | Sí |
| `dbo.registro_estetica` | 0 | 0 | Sí |
| `dbo.servicio` | 9 | 9 | Sí |
| `dbo.usuario` | 4 | 4 | Sí |
| `dbo.venta` | 211 | 211 | Sí |
