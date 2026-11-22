# Guion de prueba de aceptación de P5 «Integración y endurecimiento» (S5-18)

> Apartado 4.5.2.3 y Tabla 4.14. Es la **aceptación final** del sistema (S5-19). TA-09 la ejecutan **todo el
> personal y quien imparte la asignatura**; TA-10, **una persona que nunca ha usado el sistema**. Nadie del equipo
> de desarrollo ayuda: quien acompaña solo observa, lee los pasos y anota; no explica ni toca el teclado.
> Al terminar, los resultados pasan al registro de ejecución (`resultados_pruebas.md`, Tabla 4.19) y al acta de P5.
> El ensayo automático de TA-09 es TS-10 (`tests/sistema/test_TS10_jornada_completa.py`): recorre los mismos pasos
> con los mismos datos y los mismos totales.

| Campo | Valor |
|---|---|
| Línea base evaluada | `develop` en el commit: ______ (al cerrar P5 será `v1.0`) |
| Fecha | ____/____/2026 |
| Evaluadores y roles que representan | Recepcionista: ____________ · Veterinario: ____________ · Estilista: ____________ · Administrador: ____________ |
| Quien imparte la asignatura | ______________________ |
| Persona nueva (TA-10) | ______________________ |
| Observador | ______________________ |
| Hora de inicio / fin | ____:____ / ____:____ |

## Antes de empezar (lo prepara el observador, sin los evaluadores presentes)

1. SQL Server y Docker Desktop encendidos.
2. Si el personal va a practicar (`guia_capacitacion.md`), que lo haga **antes** de este paso: la práctica crea
   tickets que cambiarían los totales de TA-09.
3. Datos ficticios limpios **del mismo día de la prueba** (las citas y los tickets se crean con la fecha del día
   en que se cargan). En PowerShell:
   ```
   cd C:\Users\jesus\Documents\dogtor-veterinaria; .venv\Scripts\activate; python bd/ejecutar.py --recrear; python manage.py cargar_datos_prueba
   ```
4. Levantar el entorno HTTPS de producción (D-25):
   ```
   cd C:\Users\jesus\Documents\dogtor-veterinaria; docker compose up -d --build
   ```
5. Abrir **https://dogtor.local** en Chrome o Edge. Cuentas: `recepcion`, `veterinario`, `estilista` y
   `administrador` (contraseña de `.env`). Si hay una sola laptop, cada rol entra cuando le toca y al terminar
   pulsa **Cerrar sesión**.
6. Hacer **TA-09 antes que TA-10**.

Datos ficticios que usa el guion:

| Cita o ticket | Cliente | Contenido | Situación al empezar |
|---|---|---|---|
| Cita de Toby, 9:00 | Marta Ríos | Consulta general con desparasitante aplicado | Completada, **por cobrar** |
| Cita de Max, 10:00 | Elena Torres | Consulta general con Laura Medina; alérgico a la penicilina | **Programada** |
| Cita de Canela, 12:00 | Ana Lucía Vega | Baño con Mario Estrada | **Programada** |
| T-2026-00001 | Jorge Salas | Croquetas y collar, $470.00 | **Pagado** en efectivo (recibió $500.00, cambio $30.00) |
| T-2026-00002 | Pedro Ibarra | Shampoo y croquetas, $560.00 | **Pendiente**: abonó $300.00 con tarjeta, saldo $260.00 |

---

## TA-09 · Jornada simulada completa: agenda, consulta, estética, cobro y corte

**Evalúan:** todo el personal y quien imparte la asignatura · **Requisitos:** RF-01 a RF-14, RNF-03, RNF-04 ·
**Criterio de aceptación (Tabla 3.1):** el sistema supera las pruebas de aceptación.

### Apertura · Recepcionista (`recepcion`)

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Revise qué hay que hacer hoy.» | El Inicio muestra las citas de hoy (Toby, Max y Canela), **Recordatorios pendientes: 2** (1 si mañana es domingo) y **Tickets con saldo: 1** con «Por cobrar: $260.00». | | |
| 2 | «Imprima la agenda de hoy por si se va la luz.» | En **Agenda**, vista del día, **Imprimir agenda (contingencia)** abre un PDF en carta horizontal con las 3 citas, el teléfono del dueño y la alergia de Max. | | |
| 3 | «Llega una clienta nueva: Rosa Jornada Ficticia, tel. 833 555 0110, prefiere WhatsApp. Regístrela con su perrita Nube, Labrador, de 2 años y 20 kg.» | «Cliente «Rosa Jornada Ficticia» registrado.» y después «Mascota «Nube» registrada y su expediente abierto.» (sin la casilla del aviso de privacidad no deja guardar). | | |
| 4 | «Agende a Nube para una consulta general con la doctora Laura el siguiente día hábil a las 16:00.» | «Cita agendada: Nube con Laura Medina Ficticia, el …». | | |

### Consulta · Veterinario (`veterinario`)

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 5 | «Atienda a Max: viene a revisión anual y tiene tos leve; pesa 29.1 kg.» | Antes de abrir se ve la alerta roja «Alergias: Penicilina». Al abrir: «Consulta de Max abierta.» | | |
| 6 | «Aplique una dosis de vacuna antirrábica, 1 mL subcutánea, con la siguiente dosis en un año.» | «Aplicación registrada: Vacuna antirrábica, lote VAC-002-A. …» | | |
| 7 | «Recete amoxicilina: 1 tableta cada 12 horas por 7 días.» | «Receta R-2026-00001 emitida.» | | |
| 8 | «Anote temperatura 38.7, diagnóstico “Traqueítis leve”, tratamiento “Amoxicilina 7 días”, guarde y firme.» | «Consulta guardada.» y, al firmar, «Consulta firmada. La cita quedó completada y el peso de Max se actualizó a 29.10 kg.» | | |

### Estética · Estilista (`estilista`)

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 9 | «Canela ya salió del baño: pelaje sano, sin hallazgos; usó shampoo neutro. Regístrelo.» | «Atención de Canela registrada; la cita quedó completada.» | | |

### Cobro · Recepcionista (`recepcion`)

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 10 | «Revise qué citas faltan por cobrar.» | En **Ventas y caja**, «Por cobrar hoy» muestra a **Toby, Max y Canela**. | | |
| 11 | «Cobre a Toby. La dueña paga en efectivo con $800.» | «Ticket T-2026-00003 generado por $750.00.» y «Pago de $750.00 en efectivo registrado. Entregue $50.00 de cambio. Ticket pagado.» | | |
| 12 | «Cobre a Max y agregue las 14 tabletas de amoxicilina que le recetaron.» | Sin folio no deja: «…requiere receta: capture el folio de la receta (RD-12).» Con el folio **R-2026-00001**: «Ticket T-2026-00004 generado por $960.00.» (consulta $400 + aplicación de vacuna $350 + 14 × $15). | | |
| 13 | «La dueña de Max paga los $960 con tarjeta, autorización AUT 4521.» | «Pago de $960.00 en tarjeta registrado. Ticket pagado.» | | |
| 14 | «Cobre el baño de Canela por transferencia, referencia SPEI 777.» | «Ticket T-2026-00005 generado por $350.00.» y «Pago de $350.00 en transferencia registrado. Ticket pagado.» | | |
| 15 | «Rosa Jornada compra un collar ajustable mediano y paga $150 exactos en efectivo.» | Con **Nuevo ticket** → Rosa: «Ticket T-2026-00006 generado por $150.00.» y «Pago de $150.00 en efectivo registrado. Ticket pagado.» | | |
| 16 | «Pedro Ibarra viene a liquidar su ticket en efectivo.» | En T-2026-00002: «Pago de $260.00 en efectivo registrado. Ticket pagado.» El Inicio ya no tiene tickets con saldo. | | |
| 17 | «Haga el corte de caja del día e imprímalo.» | Efectivo neto **$1,630.00** (recibido $1,710.00 · cambio entregado $80.00), Tarjeta **$1,260.00**, Transferencia **$350.00**; total neto **$3,240.00**. Tickets generados: 6 (pagados 6, pendientes 0). **PDF para imprimir** abre el corte en carta. | | |

### Cierre · Administrador (`administrador`; puede ser quien imparte la asignatura)

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 18 | «Revise que el corte de hoy sea el mismo que entregó Recepción.» | Total neto **$3,240.00**, con los 7 pagos del día en el detalle. | | |
| 19 | «Revise en Inventario la amoxicilina y la vacuna antirrábica.» | Amoxicilina: lote MED-001-A en **6** (salieron 14 con la venta T-2026-00004; el que caduca primero) y MED-001-B en **40**. Vacuna antirrábica: VAC-002-A en **17**, con un solo movimiento «Aplicación −1». | | |
| 20 | «Revise en la Bitácora quién registró los cobros de hoy.» | Con **Qué** = Pago y la fecha de hoy: **5** altas hechas por la cuenta `recepcion`. | | |
| 21 | «Revise la consulta de Max.» | Se ve **Firmada**, de solo lectura; el Administrador ve el botón **Corregir (Administrador)** (pide motivo y queda en la bitácora). No corregir nada. | | |

**Al terminar TA-09 el observador** hace el respaldo del cierre con la tarea programada (la misma de las 22:00)
y anota el resultado:

```
cd C:\Users\jesus\Documents\dogtor-veterinaria; .venv\Scripts\activate; python scripts\tarea.py respaldo; Get-Content logs\tareas.log -Tail 5
```

Debe terminar con «Respaldo verificado: …» (RNF-04). ☐ Sí ☐ No

**Resultado TA-09:** ☐ Aprobado (todos los pasos «Sí» y el respaldo verificado) ☐ Fallido (anotar el paso y abrir
un DEF-nnn)

---

## TA-10 · Una persona nueva registra un cliente y cobra un ticket

**Evalúa:** una persona que nunca ha usado el sistema · **Requisito:** RNF-07 · **Criterio de aceptación
(Tabla 3.1):** tras 30 minutos de capacitación lo logra **sin ayuda en 10 minutos o menos**.

1. Capacitar a la persona con `guia_capacitacion.md` (30 minutos, con la cuenta `recepcion`). Hora de fin de la
   capacitación: ____:____ · La impartió: ______________________
2. Darle la cuenta `recepcion` con la sesión cerrada, leerle la tarea completa **una sola vez** e iniciar el
   cronómetro al decir «Empiece». Se detiene cuando aparece «Ticket pagado».

> **Tarea (leer tal cual):** «Llega Teresa Nueva Ficticia, teléfono 833 555 0120, prefiere que le escriban por
> WhatsApp y acepta el aviso de privacidad. Regístrela. Después cóbrele una bolsa de croquetas de perro adulto de
> 2 kg y un shampoo hipoalergénico; paga con un billete de $1,000 en efectivo.»

| # | Lo que debe lograr | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | Registrar a la clienta | «Cliente «Teresa Nueva Ficticia» registrado.» con el aviso de privacidad aceptado y la preferencia WhatsApp. | | |
| 2 | Generar el ticket | «Ticket T-2026-000nn generado por $560.00. Registre el pago.» ($320.00 + $240.00) | | |
| 3 | Cobrar en efectivo | «Pago de $560.00 en efectivo registrado. Entregue $440.00 de cambio. Ticket pagado.» | | |

| Medición | Valor |
|---|---|
| Hora de inicio / fin | ____:____ / ____:____ |
| Tiempo total (meta: 10 minutos o menos) | ______ min |
| Veces que pidió ayuda (meta: 0) | ______ |

**Resultado TA-10:** ☐ Aprobado (los 3 pasos «Sí», sin ayuda y en 10 minutos o menos) ☐ Fallido (anotar qué la
detuvo y abrir un DEF-nnn u OBS-nnn)

---

## Calificación del personal (Tabla 3.20: promedio de al menos 4 de 5)

Al terminar, cada evaluador califica **sin que el equipo opine** los cinco aspectos del apartado 4.5.2.3:

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| (Recepcionista) | | | | | | |
| (Veterinario) | | | | | | |
| (Estilista) | | | | | | |
| (Administrador) | | | | | | |
| (Quien imparte la asignatura) | | | | | | |
| (Persona nueva, TA-10) | | | | | | |

Observaciones de los evaluadores: ______________________________________________

## Al terminar (lo hace el líder)

1. Copiar a `docs/gestion/resultados_pruebas.md`, Tabla 4.19 (sección P5), las filas de TA-09 y TA-10 con fecha,
   ejecutores, versión (commit), resultado, el tiempo de TA-10 y, si falló, el defecto.
2. Registrar cada defecto encontrado como DEF-nnn y cada sugerencia como OBS-nnn.
3. Pasar la calificación y la decisión al acta de P5 (S5-21).
4. Apagar el entorno HTTPS si ya no se usa: `docker compose down`.
