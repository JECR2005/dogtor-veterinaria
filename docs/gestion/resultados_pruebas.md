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
mano con el guion `guion_aceptacion_P1.md`.

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

### Observaciones del personal en la evaluación

| ID | Fecha | Prototipo | Observación | Atención |
|---|---|---|---|---|
| OBS-01 | 17/11/2026 | P1 | Al generar una nueva cita, mostrar de entrada la lista de clientes con sus mascotas para elegir a simple vista, sin tener que buscar (RI-06). | Atendida el 17/11/2026 en el PR #56: lista alfabética con mascotas activas, paginada; el buscador queda como filtro. |

## Registro de defectos

Clase: **Crítico** (impide operar o compromete datos) · **Mayor** (afecta un requisito de prioridad alta sin impedir la atención) · **Menor** (presentación o comodidad).

Origen según la Tabla 4.22 (IEEE Std 1044). Todos los de P1 se corrigieron con una prueba nueva que fallaba antes.

| ID | Fecha | Caso que lo detectó | Requisito | Clase | Origen | Descripción | Causa raíz y acción preventiva | Responsable | Estado | Fecha de cierre |
|---|---|---|---|---|---|---|---|---|---|---|
| DEF-001 | 14/11/2026 | Prueba exploratoria de UI-07 (JECR2005) | RF-05, RD-02 | Mayor | Lógica de negocio | Una mascota podía tener dos citas a la misma hora con empleados distintos (la regla de empalmes solo revisaba al empleado). Corregido con D-16 (PR #46). | RD-02 solo define el empalme por empleado; se agregó la regla de la mascota y se pidió actualizar RD-02 en el documento. | Claude | Cerrado | 14/11/2026 |
| DEF-002 | 17/11/2026 | Revisión de la Tabla 4.9 al evaluar LV-03 (S1-22) | RNF-01, RI-11 | Mayor | Seguridad | El Estilista veía todos los clientes y mascotas; la Tabla 4.9 le da «○ solo la mascota de su cita». | Se programó el acceso por opción del menú, pero no las restricciones finas por registro de la Tabla 4.9. Acción: cada nota de la Tabla 4.9 tiene ahora una prueba (`test_estilista.py`). | Claude | Cerrado | 17/11/2026 |
| DEF-003 | 17/11/2026 | LV-03 punto 9 (S1-22) | RNF-01 | Mayor | Seguridad | Tras cerrar sesión, el botón Atrás podía mostrar desde la caché la última página con datos. | Faltaba indicar al navegador que no guarde las páginas con sesión. Acción: middleware `SinCacheConSesion` y su prueba. | Claude | Cerrado | 17/11/2026 |
| DEF-004 | 17/11/2026 | LV-03 punto 10 (S1-22) | RNF-07 | Menor | Interfaz | No existía la opción Ayuda con la guía de usuario (apartado 4.6.2). | La guía estaba en el documento pero no en el sistema. Acción: botón Ayuda con la guía del rol; cada prototipo agrega sus procedimientos. | Claude | Cerrado | 17/11/2026 |

## Tabla 4.20 · Resumen de resultados por prototipo

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 10 | | | | | | | | |
| P2 | 6 | | | | | | | | |
| P3 | 11 | | | | | | | | |
| P4 | 10 | | | | | | | | |
| P5 | 15 | | | | | | | | |

## Formato LV-R · Calidad por lista y prototipo (%)

| Lista de verificación | Puntos | P1 | P2 | P3 | P4 | P5 | Nivel final |
|---|---|---|---|---|---|---|---|
| LV-01 Aseguramiento de calidad | 7 | | | | | | |
| LV-02 Estándares de calidad | 6 | | | | | | |
| LV-03 Funcionalidad modular | 22 | | | | | | |
| LV-04 Funcionalidad modular, codificación | 10 | | | | | | |
| **Calidad global** | | | | | | | |
