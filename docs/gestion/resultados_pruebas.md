# Registro de resultados de pruebas (apartado 4.5.3.2)

## Formato LV-00 · Encabezado común de las listas de verificación

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Identificador | LV-0_ (en LV-03 y LV-04 agregar módulo: LV-03-AGE) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | |
| Módulo del sistema (solo LV-03 y LV-04) | SEG · CAT · AGE · EXP · INV · VEN · REC · REP |
| Objetivo | |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | | | Alta |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.

## Tabla 4.19 · Registro de ejecución de casos

La integración continua llena estas filas en cada ejecución (resumen del trabajo «pruebas» en GitHub Actions y
artefacto `reportes-pruebas`, generado con `scripts/registro_casos.py`). Las pruebas de aceptación (TA) se anotan a
mano con los guiones `guion_aceptacion_P1.md` y `guion_aceptacion_P2.md`.

### P1 · Sprint 1

| Caso | Fecha | Ejecutor | Versión (etiqueta/commit y entorno) | Resultado (Aprobado/Fallido/Bloqueado) | Defecto | Evidencia |
|---|---|---|---|---|---|---|
| TI-01 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 2 prueba(s) automatizada(s), reporte JUnit de la CI |
| TI-02 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 2 prueba(s) automatizada(s), reporte JUnit de la CI |
| TS-01 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 212 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-01 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-02 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-03 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-04 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-05 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 6 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-13 | 14/11/2026 | CI (GitHub Actions) | `e262e19` · CI, SQL Server 2022 (corrida 43660239595) | Aprobado | | 5 prueba(s) automatizada(s), reporte JUnit de la CI |
| TA-01 | 17/11/2026 | JECR2005 como Recepcionista y Administrador (evaluación sin ayuda del equipo) | `develop` en la laptop nueva (SQL Server `localhost`) | Aprobado | | Guion `guion_aceptacion_P1.md`: 8 de 8 pasos; calificación 5/5; observación OBS-01 atendida en el PR #56 |
| TA-02 | 17/11/2026 | JECR2005 como Recepcionista (evaluación sin ayuda del equipo) | `develop` en la laptop nueva (SQL Server `localhost`) | Aprobado | | Guion `guion_aceptacion_P1.md`: 5 de 5 pasos; «Empalme de horario» y «Fuera de horario laboral» con su indicación |

### P2 · Sprint 2

Desde P2 cada caso cita el riesgo de la matriz que mitiga (OBS-02, LV-01 punto 7).

| Caso | Fecha | Ejecutor | Versión (etiqueta/commit y entorno) | Resultado (Aprobado/Fallido/Bloqueado) | Defecto | Riesgo | Evidencia |
|---|---|---|---|---|---|---|---|
| TI-03 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 3 prueba(s) automatizada(s), reporte JUnit de la CI |
| TS-12 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 1 prueba automatizada (adelanto de P5: dos descuentos simultáneos del último lote), reporte JUnit de la CI |
| TU-06 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-07 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 2 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-08 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TU-09 | 18/11/2026 | CI (GitHub Actions) | `0d66bbc` · CI, SQL Server 2022 (corrida 44438931162) | Aprobado | | R08 | 1 prueba(s) automatizada(s), reporte JUnit de la CI |
| TA-03 | 18/11/2026 | JECR2005 como Administrador (evaluación sin ayuda del equipo) | `0d66bbc` (`develop`) en la laptop nueva (SQL Server 2025 `localhost`), datos ficticios recreados | Aprobado | | R04, R08 | Guion `guion_aceptacion_P2.md`: 7 de 7 pasos; calificación 4/5 |

### Observaciones del personal en la evaluación

| ID | Fecha | Prototipo | Observación | Atención |
|---|---|---|---|---|
| OBS-01 | 17/11/2026 | P1 | Al generar una nueva cita, mostrar de entrada la lista de clientes con sus mascotas para elegir a simple vista, sin tener que buscar (RI-06). | Atendida el 17/11/2026 en el PR #56: lista alfabética con mascotas activas, paginada; el buscador queda como filtro. |
| — | 18/11/2026 | P2 | Sin observaciones en TA-03. El evaluador calificó 4/5 por criterio propio («siempre se puede mejorar»), sin señalar una falla. | No requiere acción. |

## Registro de defectos

Clase: **Crítico** (impide operar o compromete datos) · **Mayor** (afecta un requisito de prioridad alta sin impedir la atención) · **Menor** (presentación o comodidad).

Origen según la Tabla 4.22 (IEEE Std 1044). Todos los de P1 se corrigieron con una prueba nueva que fallaba antes.

| ID | Fecha | Caso que lo detectó | Requisito | Clase | Origen | Descripción | Causa raíz y acción preventiva | Responsable | Estado | Fecha de cierre |
|---|---|---|---|---|---|---|---|---|---|---|
| DEF-001 | 14/11/2026 | Prueba exploratoria de UI-07 (JECR2005) | RF-05, RD-02 | Mayor | Lógica de negocio | Una mascota podía tener dos citas a la misma hora con empleados distintos (la regla de empalmes solo revisaba al empleado). Corregido con D-16 (PR #46). | RD-02 solo define el empalme por empleado; se agregó la regla de la mascota y se pidió actualizar RD-02 en el documento. | Claude | Cerrado | 14/11/2026 |
| DEF-002 | 17/11/2026 | Revisión de la Tabla 4.9 al evaluar LV-03 (S1-22) | RNF-01, RI-11 | Mayor | Seguridad | El Estilista veía todos los clientes y mascotas; la Tabla 4.9 le da «○ solo la mascota de su cita». | Se programó el acceso por opción del menú, pero no las restricciones finas por registro de la Tabla 4.9. Acción: cada nota de la Tabla 4.9 tiene ahora una prueba (`test_estilista.py`). | Claude | Cerrado | 17/11/2026 |
| DEF-003 | 17/11/2026 | LV-03 punto 9 (S1-22) | RNF-01 | Mayor | Seguridad | Tras cerrar sesión, el botón Atrás podía mostrar desde la caché la última página con datos. | Faltaba indicar al navegador que no guarde las páginas con sesión. Acción: middleware `SinCacheConSesion` y su prueba. | Claude | Cerrado | 17/11/2026 |
| DEF-004 | 17/11/2026 | LV-03 punto 10 (S1-22) | RNF-07 | Menor | Interfaz | No existía la opción Ayuda con la guía de usuario (apartado 4.6.2). | La guía estaba en el documento pero no en el sistema. Acción: botón Ayuda con la guía del rol; cada prototipo agrega sus procedimientos. | Claude | Cerrado | 17/11/2026 |
| DEF-005 | 17/11/2026 | Prueba del bloque A de P2 en la base local (JECR2005) | RD-05, D-04 | Mayor | Datos | `bd/ejecutar.py --cambio` no aplicaba el cambio a decimales: error 3997 de SQL Server porque la transacción empezaba en un lote (`GO`) y terminaba en otro, y la conexión usa MARS. Se revirtió sin cambios. Corregido en el PR #61. | Las pruebas corren dentro de una transacción abierta y no lo detectaban. Acción: script en un solo lote con TRY/CATCH y prueba de unidad que revisa que cada BEGIN TRANSACTION tenga su COMMIT en el mismo lote. | Claude | Cerrado | 17/11/2026 |
| DEF-006 | 17/11/2026 | Prueba del bloque A de P2 en la base local (JECR2005) | — (herramienta local) | Menor | Datos | `bd/ejecutar.py --recrear` se detenía en `usuario` (error 3726) porque `django_admin_log` la referencia, y dejaba la base local a medio borrar. Corregido en el PR #62. | El script de borrado no contemplaba las tablas de Django ni usaba transacción. Acción: borra también las tablas de Django, todo o nada, ejecuta `migrate` y tiene prueba de integración. | Claude | Cerrado | 17/11/2026 |
| DEF-007 | 19/11/2026 | Prueba del bloque G de P3 en la base local (JECR2005) | RD-07, RD-08, D-19 | Mayor | Datos | `bd/ejecutar.py --cambio` del cambio D-19 se detenía con el error 547: `CK_aplicacion_consulta_abierta` se agregaba WITH CHECK y la base ya tenía aplicaciones de consultas firmadas (válidas, capturadas cuando estaban abiertas). Se revirtió sin cambios. Corregido en el PR #79. | La prueba del cambio simulaba una base sin aplicaciones en consultas firmadas. Acción: restricciones WITH NOCHECK en el script incremental y la prueba ahora parte de una consulta firmada con aplicación y receta. Verificado en la base local: se aplicó dos veces sin error. | Claude | Cerrado | 19/11/2026 |

## Tabla 4.20 · Resumen de resultados por prototipo

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 10 | 10 | 10 | 100 % | 0 | 0 | 96 % | 5.0 | Cerrar |
| P2 | 6 | 6 | 6 | 100 % | 0 | 0 | 96 % | 4.0 | Cerrar |
| P3 | 11 | | | | | | | | |
| P4 | 10 | | | | | | | | |
| P5 | 15 | | | | | | | | |

## Formato LV-R · Calidad por lista y prototipo (%)

| Lista de verificación | Puntos | P1 | P2 | P3 | P4 | P5 | Nivel final |
|---|---|---|---|---|---|---|---|
| LV-01 Aseguramiento de calidad | 7 | 91 | 93 | | | | |
| LV-02 Estándares de calidad | 6 | 90 | 93 | | | | |
| LV-03 Funcionalidad modular | 22 | 94 | 93 | | | | |
| LV-04 Funcionalidad modular, codificación | 10 | 100 | 100 | | | | |
| **Calidad global** | | **94** | **95** | | | | |

El detalle de P1 (criterios de salida, LV-01 a LV-04, LV-03R y observaciones OBS-02 a OBS-06) está en `evaluacion_P1.md`;
el de P2 (LV-03-INV, LV-04-INV y revisión de las observaciones), en `evaluacion_P2.md`.
