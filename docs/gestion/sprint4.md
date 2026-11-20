# Sprint 4 · Prototipo P4 «Ventas y caja»

| Campo | Valor |
|---|---|
| Duración | 2 semanas: 20 de noviembre al 3 de diciembre de 2026 (adelantado: P3 cerró el 20/11 en lugar del 9/12) |
| Requisitos | RF-13 Ventas, pagos y corte de caja; RF-14 Cancelación de ventas; RD-06 Pagos y cierre de venta; RD-11 Precio histórico; RD-12 Venta de medicamentos con control |
| Issues (hito P4) | #13 RF-13 · #14 RF-14 · #20 RD-06 · #25 RD-11 · #26 RD-12 |
| Pantallas (Tabla 4.6) | UI-17 Ticket y cobro · UI-18 Cancelación de venta · UI-19 Corte de caja |
| Evalúan (Tabla 3.1) | Recepcionista y Administrador (JECR2005 en cada papel) |
| Criterio de validación (Tabla 3.1) | El corte de caja coincide con los pagos del día y solo el Administrador cancela un ticket pagado, con devolución y reintegro correcto del inventario. |
| Casos de prueba base (Tabla 4.17) | 10: TU-10, TU-11, TU-12, TU-18, TI-05, TI-06, TI-07, TI-12, TA-07, TA-08 |
| Responsable de calidad (`roles.md`) | Rodríguez Sánchez Nahomi Gianina |
| Línea base al cerrar | `v0.4-P4` |

## Actividades

Estado: ⬜ pendiente · 🔄 en curso · ✅ hecha. **Se trabaja por bloques:** un pull request por bloque, que JECR2005
prueba en su equipo e integra antes de pasar al siguiente.

### A. Arranque

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-01 | Plan del sprint (este archivo) | APE | Plan en `docs/gestion/` |
| ✅ | S4-02 | Decisiones de P4: formato del folio del ticket y cómo se cobra lo aplicado en consulta | RF-13, RD-09 | D-20 elegida el 20/11: folio `T-AAAA-NNNNN` (`ventas/services.py`, `siguiente_folio`, con prueba) y cobro con servicios de la categoría Aplicación, sin volver a descontar |
| ✅ | S4-03 | Datos ficticios de P4 | RF-13, RF-14 | `cargar_datos_prueba` crea T-AAAA-00001 (Jorge Salas, $470.00 pagado en efectivo con $30.00 de cambio), T-AAAA-00002 (Pedro Ibarra, $560.00 con $300.00 en tarjeta, saldo $260.00) y a Toby de Marta Ríos (datos fiscales) con consulta firmada hoy a las 9:00 y desparasitante por cobrar |

### B. Ticket

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-04 | Nuevo ticket con servicios y productos a precio vigente; el stock baja al generarlo, del lote que caduca primero y nunca de uno vencido (UI-17) | RF-13, RD-03, RD-05, RD-11 | Pantalla con pruebas · `/ventas/nuevo/`: cliente, líneas con precio y existencias a la vista, importe y total en vivo; todo o nada; TU-12 en verde |
| ✅ | S4-05 | Ticket desde una cita: trae su servicio y las aplicaciones como servicio de cobro, sin volver a descontar el lote | RD-09 | TI-05 en verde · «Por cobrar hoy» con las citas completadas sin ticket; una cita se cobra una sola vez |
| ✅ | S4-06 | Un medicamento con control solo se agrega con el folio de una receta que lo incluye | RD-12 | TU-18 y TI-07 en verde · la receta debe existir, ser de una mascota del cliente e incluir el producto |
| ✅ | S4-07 | Lista de tickets por fecha y estado; el botón «Nuevo ticket» de la barra superior de Recepción ya funciona | RF-13 | Pantalla con pruebas · `/ventas/` y detalle `/ventas/tickets/<id>/` con líneas, total, saldo y pagos |

### C. Cobro

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-08 | Pagos parciales en efectivo, tarjeta o transferencia; cálculo del cambio; el ticket pasa a «Pagada» solo con saldo cero | RF-13, RD-06 | TU-10 y TU-11 en verde · en el detalle del ticket, con el cambio en vivo; con tarjeta o transferencia se cobra como máximo el saldo |
| ✅ | S4-09 | Marca «Requiere factura» con los datos fiscales del cliente; la factura se emite fuera del sistema | RF-13, R11 | Sin RFC, régimen y código postal no se marca · la pantalla dice qué falta y lleva a la ficha del cliente |
| ✅ | S4-10 | PDF del ticket en tamaño carta | RF-13, D-18 | Se descarga el PDF con su folio · `/ventas/tickets/<id>/pdf/`, con líneas, pagos y la leyenda «no es un comprobante fiscal» |

### D. Cancelación

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-11 | Cancelar un ticket sin pagos (Recepción o Administrador) con motivo; regresan a sus lotes solo los productos vendidos (UI-18) | RF-14 | TI-06 en verde · resumen antes de confirmar (RI-04); cada pieza regresa al lote del que salió con un movimiento «Devolución»; la cita vuelve a «Por cobrar» |
| ✅ | S4-12 | Cancelar un ticket con pagos, solo el Administrador: registra la devolución de lo abonado, reintegra los productos vendidos (no los aplicados) y deja registro en la bitácora con los valores previos | RF-14, RNF-03 | La Recepcionista recibe «Acceso denegado»; adelanto de TI-09 en verde · una devolución por cada método con que se pagó |

### E. Corte de caja

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-13 | Corte del día por método de pago: abonos, devoluciones y neto (UI-19) | RF-13 | TI-12 en verde · `/ventas/corte/`: cuenta los pagos por su fecha; en efectivo, recibido y cambio entregado; resumen de tickets del día |
| ✅ | S4-14 | PDF del corte en tamaño carta y aviso de tickets con saldo pendiente en el Inicio de Recepción | RF-13 | Pantalla con pruebas · PDF con espacio para firmas de entrega y recepción; tarjeta «Tickets con saldo» en el Inicio de Recepción y Administrador; lista de pendientes de cualquier día |

### F. Interfaz y seguridad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S4-15 | Permisos de la Tabla 4.9 (Ventas: Administrador ●, Recepcionista ● sin cancelar tickets con pagos), TS-01 con las rutas nuevas y Ayuda de Recepción y Administrador | RNF-01, RNF-07 | Ningún rol ve más de lo suyo · `test_S4_15_permisos_y_ayuda.py`; TS-01 recorre las 10 rutas de Ventas; Ayuda con cobrar, cancelar, corte y problemas frecuentes de caja |

### G. Pruebas

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S4-16 | TU-10, TU-11, TU-12, TU-18 y pruebas que intentan violar RD-06, RD-11 y RD-12 (en el servicio y en la base) | RD-06, RD-11, RD-12 | Integración continua en verde |
| ⬜ | S4-17 | TI-05, TI-06, TI-07 y TI-12 | RF-13, RF-14, RD-09 | Integración continua en verde |
| ⬜ | S4-18 | Guion de TA-07 y TA-08 y su regresión automatizada | Tabla 4.14 | `guion_aceptacion_P4.md` |
| ⬜ | S4-19 | Aceptación como Recepcionista y Administrador con la calificación de los cinco aspectos | Tabla 3.1 | Aprobado, ≥ 4/5 (JECR2005) |

### H. Cierre del prototipo

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S4-20 | Criterios de salida y listas LV (hojas de VEN y REP) | Tabla 4.11 | `evaluacion_P4.md` |
| ⬜ | S4-21 | Prueba de restauración con datos de P4 | RNF-04 | < 120 min (JECR2005, en SSMS) |
| ⬜ | S4-22 | Acta de P4, Tabla 4.20, LV-R y riesgos R08, R11 y R06 | APE | Documentos en `docs/gestion/` |
| ⬜ | S4-23 | `develop` → `main` y release `v0.4-P4` | — | Línea base publicada (JECR2005 integra) |
