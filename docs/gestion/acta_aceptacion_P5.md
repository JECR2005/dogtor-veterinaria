# Acta de aceptación del prototipo P5 y del sistema (Anexo C del contrato)

> Borrador preparado el 21/11/2026 (S5-21). Las secciones 1 (primer criterio), 4, 5 y 6 se llenan el día de la
> aceptación con el guion `guion_aceptacion_P5.md` (S5-19).

| Campo | Valor |
|---|---|
| Proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P5 · nombre: Integración y endurecimiento (entrega final del sistema) |
| Línea base evaluada (etiqueta git) | v1.0 (evaluada en `develop` en el commit: ______) |
| Fecha de entrega para evaluación | ____/____/2026 |
| Fecha límite de respuesta (5 días hábiles, cláusula Sexta) | ____/____/2026 |
| Evaluadores (rol que representan) | Personal: ______________________ · Quien imparte la asignatura: ______________________ · Persona nueva (TA-10): ______________________ |
| Responsable de calidad del prototipo | Castillo Ruiz Jesus Enrique |

## 1. Criterio de validación del prototipo (Tabla 3.1)

| Criterio | Cumple (Sí/No) | Observación |
|---|---|---|
| El sistema supera las pruebas de aceptación | | TA-09: ___ de 21 pasos y respaldo verificado · TA-10: ___ min, ___ ayudas |
| Se restaura un respaldo en menos de 2 horas | Sí | TS-07: 1.02 s en un servidor limpio (SQL Server 2025 en Docker), 33 de 33 tablas con los mismos 4,498 registros y DBCC CHECKDB sin errores |
| 10 usuarios simultáneos operan sin errores | Sí | TS-06: 14,626 operaciones en 30 min con 10 usuarios, 0 errores, 99.73 % en 2 s o menos |

## 2. Requisitos incluidos y su criterio de aceptación

| Requisito | Caso(s) de prueba | Resultado | Observación |
|---|---|---|---|
| RNF-01 Seguridad | TU-13, TS-01, TS-02, TS-03 | Aprobado | Acceso por rol en 560 combinaciones; ZAP sin alertas altas; https con HSTS, cookies seguras y contraseñas con hash y sal |
| RNF-02 Compatibilidad | TS-04 | Aprobado | 14 de 14 pasos en Chrome, Edge y tableta; receta, ticket, corte y agenda en carta |
| RNF-03 Auditoría | TI-09, TS-09 | Aprobado | 17 operaciones con su cuenta y valores previos; la base no deja modificar ni borrar la bitácora (D-23) |
| RNF-04 Respaldo | TS-07 | Aprobado | Respaldo diario a las 22:00 con copia externa y 30 días; restauración en servidor limpio en 1.02 s |
| RNF-05 Rendimiento | TS-05, TS-06 | Aprobado | Búsquedas en 210 ms como máximo con 1,200 mascotas; carga de 10 usuarios sin errores |
| RNF-06 Disponibilidad | TS-08 | En curso | Monitor cada 5 min en horario; corte del 21/11 sin caídas (`disponibilidad_TS08.md`); el mes completo sigue después de `v1.0` (D-22) |
| RNF-07 Facilidad de aprendizaje | TA-10 | | Tras 30 min de capacitación: ___ min |
| RNF-08 Privacidad | TI-01, TS-09 | Aprobado | Sin aviso no se registra; la baja conserva el historial; la exportación de contactos queda en la bitácora |
| RF-01 a RF-14 (sistema integrado) | TS-10, TA-09 | | TS-10 aprobado en la CI: jornada completa con corte de $3,240.00 e inventario cuadrado |
| R07 Contingencia | TS-11 | Aprobado | Agenda impresa cada mañana y recaptura sin pérdida de datos |
| RD-05 y R08 Concurrencia | TS-12 | Aprobado | Un ticket y una aplicación de la última pieza a la vez: solo una pasa y nada queda negativo |

## 3. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado |
|---|---|---|
| Defectos críticos abiertos | 0 | 0 (DEF-008 cerrado el 21/11) |
| Defectos mayores abiertos | ≤ 3 | 0 |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 100 % (12 de 12) |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (1,465 pruebas) |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 92.9 %, LV-02 96.7 %, LV-03 96.1 %, LV-04 100 %; mínimo 80 % |
| Restauración de un respaldo (RNF-04) | < 120 min | 1.02 s |

Detalle en `evaluacion_P5.md`; registro de casos y defectos en `resultados_pruebas.md`.

## 4. Calificación del personal (meta ≥ 4 de 5)

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| Recepcionista | | | | | | |
| Veterinario | | | | | | |
| Estilista | | | | | | |
| Administrador | | | | | | |
| Quien imparte la asignatura | | | | | | |
| Persona nueva (TA-10) | | | | | | |

Comentario de los evaluadores (____/____/2026): ______________________________________________

## 5. Observaciones del personal

| ID | Observación | Atención |
|---|---|---|
| | | |

## 6. Decisión

- [ ] **Aceptado**
- [ ] **Aceptado con observaciones** (se atienden en operación; ver issues: ___ )
- [ ] **No aceptado** (motivo):

| Por EL CLIENTE | Por EL EQUIPO |
|---|---|
| Nombre, cargo y firma: ______________________ | Castillo Ruiz Jesus Enrique, líder del proyecto y responsable de calidad de P5 · firma: ______________________ |
| Quien imparte la asignatura · firma: ______________________ | Rodríguez Sánchez Nahomi Gianina · firma: ______________________ |
