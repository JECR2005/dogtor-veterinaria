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
| TA-01 | | | | Pendiente | | Guion `guion_aceptacion_P1.md` |
| TA-02 | | | | Pendiente | | Guion `guion_aceptacion_P1.md` |

## Registro de defectos

Clase: **Crítico** (impide operar o compromete datos) · **Mayor** (afecta un requisito de prioridad alta sin impedir la atención) · **Menor** (presentación o comodidad).

| ID | Fecha | Caso que lo detectó | Requisito | Clase | Descripción | Responsable | Estado | Fecha de cierre |
|---|---|---|---|---|---|---|---|---|
| DEF-001 | 14/11/2026 | Prueba exploratoria de UI-07 (JECR2005) | RF-05, RD-02 | Mayor | Una mascota podía tener dos citas a la misma hora con empleados distintos (la regla de empalmes solo revisaba al empleado). Corregido con D-16. | Claude | Cerrado | 14/11/2026 |

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
