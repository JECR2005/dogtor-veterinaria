# Sprint 2 · Prototipo P2 «Abastecimiento»

| Campo | Valor |
|---|---|
| Duración | 2 semanas: 18 de noviembre al 1 de diciembre de 2026 (adelantado: P1 cerró el 17/11 en lugar del 4/12) |
| Requisitos | RF-11 Gestión de inventario, RF-12 Proveedores y pedidos de compra, RD-03 Restricción por caducidad, RD-05 Selección de lote y stock disponible |
| Issues (hito P2) | #11 RF-11 · #12 RF-12 · #17 RD-03 · #19 RD-05 |
| Pantallas (Tabla 4.6) | UI-08 Productos, lotes y alertas · UI-09 Proveedores y pedidos · UI-10 Recepción de pedido |
| Evalúa (Tabla 3.1) | Administrador (JECR2005 en ese papel) |
| Criterio de validación (Tabla 3.1) | Un pedido recibido crea lotes con caducidad, las existencias aumentan y aparecen las alertas de stock mínimo y de caducidad a 30 días. |
| Casos de prueba base (Tabla 4.17) | 6: TU-06, TU-07, TU-08, TU-09, TI-03, TA-03 |
| Responsable de calidad (`roles.md`) | Nuñez Hernandez Ricardo |
| Línea base al cerrar | `v0.2-P2` |

## Actividades

Estado: ⬜ pendiente · 🔄 en curso · ✅ hecha. **Se trabaja por bloques:** un pull request por bloque, que JECR2005
prueba en su equipo e integra antes de pasar al siguiente.

### A. Arranque

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S2-01 | Plan del sprint (este archivo), S1-25 marcada en `sprint1.md` | APE | Plan en `docs/gestion/` · PR #60 |
| ✅ | S2-02 | Decisión D-04: existencias y movimientos con 2 decimales | D-04, RD-05 | Opción (b) elegida el 17/11; `bd/01_tablas.sql`, script `bd/cambios/2026-11-17_RD-05_cantidad_decimal.sql`, modelo y migración 0002, con pruebas que convierten una base existente · PR #60, corregido en #61 (DEF-005) y probado en la base local el 17/11 |
| ✅ | S2-03 | Datos ficticios de P2 | RF-11, RF-12, RD-03, RD-05 | `cargar_datos_prueba` crea proveedores con RFC, 11 productos (uno en mL), lotes vigentes, por caducar, vencido y sin caducidad, un ajuste con motivo y 3 pedidos (2 pendientes, 1 cancelado) · PR #60; `--recrear` corregido en #62 (DEF-006) |

### B. Catálogos de abastecimiento

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S2-04 | Proveedores: lista, alta, edición y baja con RFC válido (UI-09) | RF-12 | Pantallas con pruebas · `/compras/proveedores/`, PR #64 |
| ✅ | S2-05 | Productos: lista con distintivos de stock bajo y por caducar; alta y edición con código único, precio y stock mínimo (UI-08) | RF-11 | Pantallas con pruebas · `/inventario/productos/`, PR #64; existencias iguales a `vista_stock_disponible` |

### C. Inventario

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S2-06 | Reglas de lote: vencido y stock disponible | RD-03, RD-05 | TU-06 y TU-07 en verde · `Lote.esta_vencido`, `stock_disponible`, `lotes_vigentes` |
| ✅ | S2-07 | Descuento del lote que caduca primero, con bloqueo si falta stock y protección ante operaciones simultáneas | RD-05 | TU-08 y TU-09 en verde; servicio listo para P3 y P4 · `inventario.services.descontar` con bloqueo de filas |
| ✅ | S2-08 | Lotes por producto y movimientos: entradas, salidas y ajustes con motivo (UI-08) | RF-11 | Cada movimiento queda registrado y no se modifica (RD-07) · ficha `/inventario/productos/<id>/` con kardex; ajuste con confirmación (RI-04) |
| ✅ | S2-09 | Alertas de stock mínimo y de caducidad a 30 días, también en el Inicio del Administrador | RF-11 | Alertas correctas con los datos de prueba · `/inventario/alertas/` y tarjeta del Inicio |

### D. Compras

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S2-10 | Pedido de compra con partidas y total; estados Pendiente y Cancelado (UI-09) | RF-12 | Pedido guardado con su total · `/compras/pedidos/`; «Pedir» desde las alertas |
| ✅ | S2-11 | Recepción: número de lote y caducidad por partida; al marcar Recibido se crean los lotes y sus entradas en una sola transacción (UI-10) | RF-11, RF-12 | TI-03 en verde · `/compras/pedidos/<id>/recibir/`; si una partida falla no se crea ningún lote |

### E. Interfaz y seguridad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S2-12 | Menús Inventario y Compras solo para el Administrador; TS-01 con las rutas nuevas; Ayuda ampliada | RNF-01, RNF-07 | Ningún otro rol entra · menú y TS-01 desde los bloques B a D; Ayuda del Administrador con inventario, compras y problemas frecuentes |

### F. Pruebas

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S2-13 | TU-06 a TU-09 y pruebas que intentan violar RD-03 y RD-05 también en la base | RD-03, RD-05 | Integración continua en verde |
| ⬜ | S2-14 | TI-03: recibir un pedido con dos productos | RF-11, RF-12 | Integración continua en verde |
| ⬜ | S2-15 | Guion de TA-03 y su regresión automatizada | Tabla 4.14 | `guion_aceptacion_P2.md` |
| ⬜ | S2-16 | Aceptación TA-03 con el Administrador y calificación de los cinco aspectos | Tabla 3.1 | Aprobado, ≥ 4/5 (JECR2005) |

### G. Cierre del prototipo

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S2-17 | Criterios de salida, listas LV (hojas de INV) y revisión de OBS-02 y OBS-03 de P1 | Tabla 4.11 | `evaluacion_P2.md` |
| ⬜ | S2-18 | Prueba de restauración con datos de P2 | RNF-04 | < 120 min (JECR2005, en SSMS) |
| ⬜ | S2-19 | Acta de P2, Tabla 4.20, LV-R y riesgos R05 y R08 | APE | Documentos en `docs/gestion/` |
| ⬜ | S2-20 | `develop` → `main` y release `v0.2-P2` | — | Línea base publicada (JECR2005 integra) |

## Forma de trabajo en este sprint

- Una rama `feature/s2-<bloque>` y un pull request a `develop` por bloque; la integración continua debe quedar en
  verde antes de integrarlo.
- JECR2005 revisa cada pull request (revisión entre pares, Tabla 3.20) y lo prueba en su entorno local.
- Los cambios al esquema siguen `bd/cambios/LEEME.md`.
