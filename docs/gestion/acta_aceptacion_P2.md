# Acta de aceptación del prototipo P2 (Anexo C del contrato)

| Campo | Valor |
|---|---|
| Proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P2 · nombre: Abastecimiento |
| Línea base evaluada (etiqueta git) | v0.2-P2 |
| Fecha de entrega para evaluación | 18/11/2026 |
| Fecha límite de respuesta (5 días hábiles, cláusula Sexta) | 25/11/2026 |
| Evaluadores (rol que representan) | Castillo Ruiz Jesus Enrique, en el papel de Administrador (Tabla 3.1) |
| Responsable de calidad del prototipo | Nuñez Hernandez Ricardo |

## 1. Criterio de validación del prototipo (Tabla 3.1)

| Criterio | Cumple (Sí/No) | Observación |
|---|---|---|
| Un pedido recibido crea lotes con caducidad y las existencias aumentan | Sí | TA-03 pasos 4 y 5: PC-0001 crea VTF-2701 y AMX-2701; vacuna triple felina de 3 a 23, amoxicilina de 60 a 120 |
| Aparecen las alertas de stock mínimo y de caducidad a 30 días | Sí | TA-03 pasos 1 y 6: las alertas aparecen y se recalculan al recibir |

## 2. Requisitos incluidos y su criterio de aceptación

| Requisito | Caso(s) de prueba | Resultado | Observación |
|---|---|---|---|
| RF-11 Gestión de inventario | TI-03, TA-03 | Aprobado | Distintivos de caducidad y stock bajo; entradas, salidas y ajustes con motivo |
| RF-12 Proveedores y pedidos de compra | TI-03, TA-03 | Aprobado | Al pasar a «Recibido» se crean los lotes y suben las existencias |
| RD-03 Restricción por caducidad | TU-06, TA-03 | Aprobado | Los lotes vencidos no se descuentan ni se reciben |
| RD-05 Selección de lote y stock disponible | TU-07 a TU-09, TS-12 (adelanto) | Aprobado | Primero el lote que caduca antes; nunca existencias negativas |

## 3. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado |
|---|---|---|
| Defectos críticos abiertos | 0 | 0 |
| Defectos mayores abiertos | ≤ 3 | 0 |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 100 % (2 de 2) |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 %, LV-02 93 %, LV-03-INV 93 %, LV-04-INV 100 %; mínimo 80 % |
| Restauración de un respaldo (RNF-04) | < 120 min | 0.56 s |

Detalle en `evaluacion_P2.md`; registro de casos y defectos en `resultados_pruebas.md`.

## 4. Calificación del personal (meta ≥ 4 de 5)

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| Administrador (JECR2005) | 4 | 4 | 4 | 4 | 4 | 4.0 |

Comentario del evaluador (18/11/2026): «Es bastante intuitivo». Califica con 4 por criterio propio, porque
considera que todo sistema puede mejorar; no señaló fallas ni sugerencias.

## 5. Observaciones del personal

| ID | Observación | Atención |
|---|---|---|
| — | Sin observaciones. El evaluador aprobó además la paleta de colores (OBS-03 de P1). | — |

## 6. Decisión

- [x] **Aceptado**
- [ ] **Aceptado con observaciones** (se atienden en el prototipo siguiente; ver issues: ___ )
- [ ] **No aceptado** (motivo):

| Por EL CLIENTE | Por EL EQUIPO |
|---|---|
| Nombre, cargo y firma: ______________________ | Castillo Ruiz Jesus Enrique, líder del proyecto · firma: ______________________ |
| | Nuñez Hernandez Ricardo, responsable de calidad de P2 · firma: ______________________ |
