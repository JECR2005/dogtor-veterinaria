# Acta de aceptación del prototipo P4 (Anexo C del contrato)

| Campo | Valor |
|---|---|
| Proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P4 · nombre: Ventas y caja |
| Línea base evaluada (etiqueta git) | v0.4-P4 (evaluada en la rama del bloque G, integrada en `develop` como `9d59244`) |
| Fecha de entrega para evaluación | 20/11/2026 |
| Fecha límite de respuesta (5 días hábiles, cláusula Sexta) | 27/11/2026 |
| Evaluadores (rol que representan) | Castillo Ruiz Jesus Enrique, en el papel de Recepcionista y Administrador (Tabla 3.1) |
| Responsable de calidad del prototipo | Rodríguez Sánchez Nahomi Gianina |

## 1. Criterio de validación del prototipo (Tabla 3.1)

| Criterio | Cumple (Sí/No) | Observación |
|---|---|---|
| El corte de caja coincide con los pagos del día | Sí | TA-07 paso 7: efectivo $920.00, tarjeta $300.00 y transferencia $400.00, total neto $1,620.00, igual a los cinco abonos del día |
| Solo el Administrador cancela un ticket pagado | Sí | TA-08 pasos 1 y 2: la Recepcionista no tiene el botón y por dirección directa recibe «Acceso denegado» |
| Con devolución y reintegro correcto del inventario | Sí | TA-08 pasos 4 y 5: devolución de $470.00 en efectivo; croquetas de 30 a 31 y collar de 11 a 12, a su lote de origen |

## 2. Requisitos incluidos y su criterio de aceptación

| Requisito | Caso(s) de prueba | Resultado | Observación |
|---|---|---|---|
| RF-13 Ventas, pagos y corte de caja | TU-10, TU-11, TI-06, TI-12, TA-07 | Aprobado | El stock baja al generar el ticket; pagos parciales con cambio; «Requiere factura»; PDF del ticket y del corte |
| RF-14 Cancelación de ventas | TI-06, TA-08 | Aprobado | Con pagos, solo el Administrador; devolución, reintegro de lo vendido y bitácora |
| RD-06 Pagos y cierre de venta | TU-10, TU-11 | Aprobado | El pago no excede el saldo; «Pagada» solo con saldo cero; también lo exige la base |
| RD-11 Precio histórico | TU-12 | Aprobado | La línea conserva el precio; la base impide cambiarlo (D-21) |
| RD-12 Venta de medicamentos con control | TU-18, TI-07 | Aprobado | Solo con el folio de una receta del cliente que incluye el producto; también lo exige la base (D-21) |
| RD-09 Descuento único (cobro de lo aplicado) | TI-05, TA-07 | Aprobado | Lo aplicado se cobra con un servicio y el lote no vuelve a bajar (D-20) |

## 3. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado |
|---|---|---|
| Defectos críticos abiertos | 0 | 0 |
| Defectos mayores abiertos | ≤ 3 | 0 |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 100 % (3 de 3) |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 %, LV-02 97 %, LV-03-VEN 94 %, LV-03-REP 94 %, LV-04 100 %; mínimo 80 % |
| Restauración de un respaldo (RNF-04) | < 120 min | Pendiente (S4-21) |

Detalle en `evaluacion_P4.md`; registro de casos y defectos en `resultados_pruebas.md`.

## 4. Calificación del personal (meta ≥ 4 de 5)

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| Recepcionista (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |
| Administrador (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |

Comentario del evaluador (20/11/2026): ambas pruebas salieron exitosas; sin sugerencias.

## 5. Observaciones del personal

| ID | Observación | Atención |
|---|---|---|
| — | Sin observaciones. | — |

## 6. Decisión

- [x] **Aceptado**
- [ ] **Aceptado con observaciones** (se atienden en el prototipo siguiente; ver issues: ___ )
- [ ] **No aceptado** (motivo):

| Por EL CLIENTE | Por EL EQUIPO |
|---|---|
| Nombre, cargo y firma: ______________________ | Castillo Ruiz Jesus Enrique, líder del proyecto · firma: ______________________ |
| | Rodríguez Sánchez Nahomi Gianina, responsable de calidad de P4 · firma: ______________________ |
