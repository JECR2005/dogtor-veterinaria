# Acta de aceptación del prototipo P3 (Anexo C del contrato)

| Campo | Valor |
|---|---|
| Proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P3 · nombre: Núcleo clínico y estética |
| Línea base evaluada (etiqueta git) | v0.3-P3 (evaluada en `develop`, commit `a8ce01e`) |
| Fecha de entrega para evaluación | 20/11/2026 |
| Fecha límite de respuesta (5 días hábiles, cláusula Sexta) | 27/11/2026 |
| Evaluadores (rol que representan) | Castillo Ruiz Jesus Enrique, en el papel de Veterinario, Recepcionista y Estilista (Tabla 3.1) |
| Responsable de calidad del prototipo | Aguilar Castillo Hugo Enrique |

## 1. Criterio de validación del prototipo (Tabla 3.1)

| Criterio | Cumple (Sí/No) | Observación |
|---|---|---|
| El veterinario firma una consulta con una vacuna y una receta | Sí | TA-04 pasos 1 a 7: consulta de Max con vacuna antirrábica y receta R-2026-00001, firmada por la veterinaria con cédula |
| El lote baja una sola vez y la receta no descuenta existencias | Sí | TA-04 pasos 8 y 9: VAC-002-A de 18 a 17 con un solo movimiento «Aplicación −1»; amoxicilina sin cambio (60) |
| La recepcionista ve el recordatorio 3 días antes de la próxima dosis | Sí | TA-05 pasos 1 y 2: Michi aparece «en 3 días» con el teléfono de Jorge Salas; Rocky (4 días) todavía no |

## 2. Requisitos incluidos y su criterio de aceptación

| Requisito | Caso(s) de prueba | Resultado | Observación |
|---|---|---|---|
| RF-06 Consulta e historial clínico | TU-14, TI-08, TA-04 | Aprobado | La firma completa la cita, actualiza el peso y deja la consulta en solo lectura; alergias visibles |
| RF-07 Emisión de recetas | TU-15, TA-04 | Aprobado | Folio consecutivo y PDF en tamaño carta; no descuenta existencias |
| RF-08 Aplicaciones | TU-16, TI-04, TA-04 | Aprobado | Lote sugerido por caducidad; próxima fecha obligatoria en vacunas y desparasitantes |
| RF-09 Recordatorios | TU-17, TI-10, TA-05 | Aprobado | Canal preferido con el mensaje listo; Contactado sale de los pendientes |
| RF-10 Atención de estética | TI-11, TA-06 | Aprobado | El aviso aparece en el Inicio del veterinario y el registro en el historial |
| RD-01 Cédula profesional | TU-05, TA-04 | Aprobado | Solo firma y receta un veterinario con cédula; la base no deja quitarla |
| RD-07 Consulta firmada en solo lectura | TU-14 | Aprobado | También la base la protege (D-19) |
| RD-08 Receta en consulta abierta | TU-15 | Aprobado | También la base lo exige (D-19) |
| RD-09 Descuento único de lo aplicado | TI-04, TA-04 | Aprobado | Ni firmar ni recetar vuelven a descontar |

## 3. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado |
|---|---|---|
| Defectos críticos abiertos | 0 | 0 |
| Defectos mayores abiertos | ≤ 3 | 0 |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 100 % (4 de 4) |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 %, LV-02 95 %, LV-03-EXP 93 %, LV-03-REC 93 %, LV-04 100 %; mínimo 80 % |
| Restauración de un respaldo (RNF-04) | < 120 min | 1.84 s |

Detalle en `evaluacion_P3.md`; registro de casos y defectos en `resultados_pruebas.md`.

## 4. Calificación del personal (meta ≥ 4 de 5)

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| Veterinario (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |
| Recepcionista (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |
| Estilista (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |

Comentario del evaluador (20/11/2026): «Todas las pruebas pasaron con un 4 de 5, no hay sugerencias de momento».
La calificación se dio como 4 de 5 en general y se registra igual en los cinco aspectos de cada rol.

## 5. Observaciones del personal

| ID | Observación | Atención |
|---|---|---|
| — | Sin observaciones. La revisión en tableta (OBS-04 de P1) se hizo el 19/11/2026 y resultó correcta. | — |

## 6. Decisión

- [x] **Aceptado**
- [ ] **Aceptado con observaciones** (se atienden en el prototipo siguiente; ver issues: ___ )
- [ ] **No aceptado** (motivo):

| Por EL CLIENTE | Por EL EQUIPO |
|---|---|
| Nombre, cargo y firma: ______________________ | Castillo Ruiz Jesus Enrique, líder del proyecto · firma: ______________________ |
| | Aguilar Castillo Hugo Enrique, responsable de calidad de P3 · firma: ______________________ |
