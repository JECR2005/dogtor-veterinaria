# Guion de prueba de aceptación de P4 «Ventas y caja» (S4-18)

> Apartado 4.5.2.3 y Tabla 4.14. La ejecuta quien evalúa el prototipo, **sin ayuda del equipo de desarrollo**,
> en el entorno local con los datos ficticios. Quien acompaña solo observa y anota; no explica ni toca el teclado.
> Al terminar, los resultados pasan al registro de ejecución (`resultados_pruebas.md`, Tabla 4.19) y al acta de P4.
> La regresión automática de este guion está en `tests/sistema/test_TA_escenarios_P4.py`.

| Campo | Valor |
|---|---|
| Línea base evaluada | `develop` en el commit: ______ (en P4 cerrado será `v0.4-P4`) |
| Fecha | ____/____/2026 |
| Evaluador y roles que representa | ______________________ (Recepcionista y Administrador) |
| Observador | ______________________ |
| Hora de inicio / fin | ____:____ / ____:____ |

## Antes de empezar (lo prepara el observador, sin el evaluador presente)

1. SQL Server encendido.
2. Datos ficticios limpios **del mismo día de la prueba** (los tickets y la consulta de Toby se crean con la fecha
   del día en que se cargan):
   ```
   .venv\Scripts\activate
   python bd/ejecutar.py --recrear
   python manage.py cargar_datos_prueba
   python manage.py runserver
   ```
3. Abrir `http://127.0.0.1:8000`. Cuentas: `recepcion` y `administrador` (contraseña de `.env`).
4. Hacer **TA-07 antes que TA-08**: los totales del corte de TA-08 dan por hecho que TA-07 ya se hizo.

Datos ficticios que usa el guion:

| Ticket o cita | Cliente | Contenido | Situación al empezar |
|---|---|---|---|
| T-2026-00001 | Jorge Salas | Croquetas perro adulto 2 kg y collar ajustable mediano, $470.00 | **Pagado** en efectivo (recibió $500.00, cambio $30.00) |
| T-2026-00002 | Pedro Ibarra | Shampoo hipoalergénico y croquetas perro adulto 2 kg, $560.00 | **Pendiente**: abonó $300.00 con tarjeta, saldo $260.00 |
| Cita de Toby, 9:00 | Marta Ríos (con datos fiscales) | Consulta general con desparasitante aplicado | Completada, **por cobrar** |

---

## TA-07 · Hacer el corte de caja de un día con pagos parciales

**Evalúan:** Recepcionista y Administrador · **Requisitos:** RF-13, RD-06, RD-09, RD-11 · **Criterio de aceptación
(Tabla 3.1):** el corte de caja coincide con los pagos del día.

Entrar como **recepcion**. Leer cada paso al evaluador **tal como está escrito** y anotar el resultado.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Revise en el Inicio cuánto falta por cobrar.» | La tarjeta **Tickets con saldo** dice **1** y «Por cobrar: $260.00». | | |
| 2 | «Cobre la consulta de Toby, que acaba de salir.» | En Ventas y caja, «Por cobrar hoy» muestra a Toby; **Cobrar** propone Consulta general $400.00 y Aplicación de desparasitante $350.00. Al generar: «Ticket T-2026-00003 generado por $750.00. Registre el pago.» | | |
| 3 | «La dueña pide factura.» | Con **Marcar «Requiere factura»**: «…requiere factura con los datos fiscales de Marta Ríos.» y se ve su RFC RIFM850312AB4. | | |
| 4 | «Paga $400 por transferencia, referencia SPEI 123456.» | «Pago de $400.00 en transferencia registrado. Saldo: $350.00.» | | |
| 5 | «El resto lo paga en efectivo con un billete de $500.» | Antes de guardar se ve «Cambio: $150.00». Al registrar: «Pago de $350.00 en efectivo registrado. Entregue $150.00 de cambio. Ticket pagado.» | | |
| 6 | «Pedro Ibarra viene a abonar $100 en efectivo a su ticket.» | En T-2026-00002: «Pago de $100.00 en efectivo registrado. Saldo: $160.00.» | | |
| 7 | «Haga el corte de caja del día.» | Efectivo neto **$920.00** (recibido $1,100.00 · cambio entregado $180.00), Tarjeta **$300.00**, Transferencia **$400.00**; total neto **$1,620.00**. Tickets generados: 3 (pagados 2, pendientes 1). | | |
| 8 | «Imprima el corte.» | **PDF para imprimir** abre el corte en tamaño carta con la tabla por método, el detalle y los espacios de firma. | | |
| 9 | «Revise otra vez el Inicio.» | **Tickets con saldo** sigue en **1**, ahora con «Por cobrar: $160.00». | | |

Cerrar sesión y entrar como **administrador**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 10 | «Revise el corte de hoy y compárelo con los pagos de cada ticket.» | El corte muestra el mismo total neto **$1,620.00**; en la lista de pagos del corte están los 5 abonos del día (T-2026-00001, -00002 dos veces y -00003 dos veces). | | |

**Resultado TA-07:** ☐ Aprobado (todos los pasos «Sí») ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## TA-08 · Intentar cancelar un ticket pagado con cada rol

**Evalúan:** Recepcionista y Administrador · **Requisitos:** RF-14, RNF-03 · **Criterio de aceptación (Tabla 3.1):**
la Recepcionista no puede; el Administrador sí, con devolución y reintegro correcto del inventario.

Entrar como **recepcion**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Jorge Salas devuelve su compra de hoy. Cancele su ticket.» | En T-2026-00001 (Pagada) no hay botón para cancelar; dice «Este ticket tiene pagos ($470.00): solo el Administrador lo puede cancelar.» | | |
| 2 | (Lo pide el observador) «Agregue `cancelar/` al final de la dirección del ticket.» | «Acceso denegado». | | |

Cerrar sesión y entrar como **administrador**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 3 | «Antes de cancelar, revise las existencias de las croquetas perro adulto y del collar mediano.» | En Inventario: Croquetas perro adulto 2 kg **30** y Collar ajustable mediano **11**. | | |
| 4 | «Cancele el ticket de Jorge Salas; el motivo es “Producto defectuoso”.» | El resumen dice «devolución de $470.00 en efectivo», «Regresan 1 Bolsa de Croquetas perro adulto 2 kg al lote ALI-001-A» y «Regresan 1 Pieza de Collar ajustable mediano al lote ACC-001-A». Al confirmar: «Ticket T-2026-00001 cancelado. Quedó registrado en la bitácora.»; el ticket queda **Cancelado**, sin botones, y en Pagos aparece la **Devolución** de $470.00. | | |
| 5 | «Revise otra vez las existencias.» | Croquetas **31** y collar **12**; en Movimientos de cada uno, una **Devolución** con la referencia «Cancelación T-2026-00001». | | |
| 6 | «Revise el corte de caja de hoy.» | Efectivo: devoluciones **$470.00** y neto **$450.00**; total neto **$1,150.00** (si TA-07 se hizo antes). | | |

**Resultado TA-08:** ☐ Aprobado ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## Calificación del personal (Tabla 3.20: promedio de al menos 4 de 5)

Al terminar, el evaluador califica **sin que el equipo opine** los cinco aspectos del apartado 4.5.2.3, una fila por
cada rol que representó:

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| (Recepcionista) | | | | | | |
| (Administrador) | | | | | | |

Observaciones del evaluador: ______________________________________________

## Al terminar (lo hace el líder)

1. Copiar a `docs/gestion/resultados_pruebas.md`, Tabla 4.19 (sección P4), las filas de TA-07 y TA-08 con fecha,
   ejecutor, versión (commit), resultado y, si falló, el defecto.
2. Registrar cada defecto encontrado como DEF-nnn y cada sugerencia como OBS-nnn.
3. Pasar la calificación al acta de P4 (sección 4).
