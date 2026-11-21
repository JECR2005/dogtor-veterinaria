# Sprint 5 · Prototipo P5 «Integración y endurecimiento»

| Campo | Valor |
|---|---|
| Duración | 2 semanas: 20 de noviembre al 3 de diciembre de 2026 (adelantado: P4 cerró el 20/11); entrega académica el 1/12 |
| Requisitos | RNF-02 Compatibilidad, RNF-03 Auditoría, RNF-04 Respaldo, RNF-05 Rendimiento, RNF-06 Disponibilidad, RNF-07 Facilidad de aprendizaje, RNF-08 Privacidad; cierre de RNF-01 |
| Issues (hito P5) | #28 RNF-02 · #30 RNF-04 · #31 RNF-05 · #32 RNF-06 · #33 RNF-07 (y #27, #29, #34 de RNF-01, RNF-03 y RNF-08, que se completan aquí) |
| Pantallas (Tabla 4.6) | UI-20 Bitácora y exportación |
| Evalúan (Tabla 3.1) | Todo el personal y quien imparte la asignatura |
| Criterio de validación (Tabla 3.1) | El sistema supera las pruebas de aceptación, se restaura un respaldo en menos de 2 horas y 10 usuarios simultáneos operan sin errores. |
| Casos de prueba base (Tabla 4.17) | 15: TI-09, TS-01 a TS-12, TA-09, TA-10 |
| Responsable de calidad (`roles.md`) | Castillo Ruiz Jesus Enrique, con revisión cruzada del equipo |
| Línea base al cerrar | `v1.0` |

## Actividades

Estado: ⬜ pendiente · 🔄 en curso · ✅ hecha. **Se trabaja por bloques:** un pull request por bloque, que JECR2005
prueba en su equipo e integra antes de pasar al siguiente.

### A. Arranque

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S5-01 | Plan del sprint (este archivo) | APE | Plan en `docs/gestion/` |
| ✅ | S5-02 | Decisiones de P5: herramientas de prueba (Playwright, Locust, OWASP ZAP), cómo medir la disponibilidad en el tiempo que queda y entorno con https | RNF-01, RNF-05, RNF-06 | D-22 elegida el 21/11: las tres herramientas (ZAP en Docker); https con Docker Desktop en la laptop (Nginx + Gunicorn + certificado local, Tabla 4.2); TS-08 en periodo reducido con un monitor programado de `/salud/` cada 5 min en horario, y el mes completo después de `v1.0` |
| ✅ | S5-03 | Datos de volumen: más de 1,000 mascotas, con tickets y consultas de varios días | RNF-05 | `cargar_datos_prueba --mascotas 1200 --historial 30`: 8 consultas firmadas con su ticket pagado por día hábil, folios `H-AAAAMMDD-NN`; `test_S5_03_datos_de_volumen.py` comprueba que los escenarios de hoy (agenda, cobro, caja, inventario, avisos y siguiente folio) quedan iguales |

### B. Bitácora y privacidad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S5-04 | Registro en la bitácora, con los valores previos, de los cambios en ventas, consultas, recetas e inventario | RNF-03 | La emisión de una receta, la firma, los ajustes, los cobros y las cancelaciones quedan registrados · D-23: 17 operaciones con su cuenta y valores previos; la base ya no deja modificar ni borrar la bitácora (cambio `2026-11-21_RNF-03_bitacora_inmutable.sql`); `test_S5_04_bitacora_de_cambios.py` y `test_D23_bitacora_en_la_base.py` |
| ✅ | S5-05 | UI-20 Bitácora: consulta por fecha, usuario y acción, y exportación que también queda registrada | RNF-03 | Solo el Administrador; TI-09 completo en verde · `/bitacora/` con filtros, valores previos y páginas de 50; CSV de lo filtrado; `test_TI09_cancelar_ticket_pagado.py` |
| ✅ | S5-06 | Exportar contactos, solo el Administrador y registrado en la bitácora; los clientes dados de baja no salen | RNF-08 | TS-09 en verde · desde la Bitácora (y un acceso en Clientes), con confirmación del aviso de privacidad; `test_TS09_privacidad_y_bitacora.py` |
| ✅ | S5-07 | Corrección de una consulta firmada por el Administrador, con motivo y registro en la bitácora (la puerta que dejó D-19) | RD-07, RNF-03 | La corrección guarda los valores previos; nadie más puede corregir · botón «Corregir (Administrador)» en la consulta firmada; la consulta muestra sus correcciones; la puerta se cierra al terminar |

### C. Respaldos y disponibilidad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S5-08 | Respaldo diario programado (Programador de tareas de Windows) con copia externa y 30 días de conservación; también la tarea diaria de recordatorios | RNF-04, RF-09 | Tareas creadas y probadas en la laptop · D-24: `scripts/programar_tareas.ps1` creó las tres tareas el 21/11; la prueba dejó «respaldo: OK» (12.1 MB en 0.4 s, copia en OneDrive) y «recordatorios: OK» en `logs/tareas.log` |
| ✅ | S5-09 | TS-07: restauración en un servidor limpio, comparando el número de registros de cada tabla | RNF-04 | Menos de 120 min y conteos iguales · 1.02 s en SQL Server 2025 en Docker; 33 de 33 tablas con los mismos 4,498 registros y DBCC CHECKDB sin errores (`ts07_restauracion.md`) |
| 🔄 | S5-10 | TS-08: monitor programado de `/salud/` en horario de atención (D-22) | RNF-06 | Monitor activo y reporte del periodo medido · tarea activa desde el 21/11 (`scripts/monitor.py`); el reporte `disponibilidad_TS08.md` se genera al cierre del sprint |

### D. Seguridad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S5-11 | TS-02: texto malicioso (scripts, inyección SQL) en formularios y buscadores, con pruebas automáticas y OWASP ZAP | RNF-01 | Ninguna entrada altera la base ni se ejecuta en la página · `test_TS02_entradas_maliciosas.py` (5 inyecciones en todos los filtros con 3 roles, scripts en formularios, inicio de sesión y revisión del código) y ZAP el 21/11: 0 FAIL, 0 altos, 140 PASS; las alertas bajas se corrigieron y las medias quedan justificadas (`docs/gestion/zap/`) |
| ✅ | S5-12 | TS-03: entorno con https en Docker (D-22), cookies seguras, cabeceras de seguridad, contraseñas con hash y sal, fin de D-15 y revisión de dependencias | RNF-01, R10 | `manage.py check --deploy` sin avisos; sin vulnerabilidades altas en las dependencias · D-25: https://dogtor.local en la laptop desde el 21/11 (Nginx + Gunicorn + mkcert, cuenta `dogtor_web`); CI: «no issues» en `check --deploy` y «No known vulnerabilities found» en pip-audit |

### E. Rendimiento

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| 🔄 | S5-13 | TS-05: búsquedas de clientes, mascotas y productos con más de 1,000 mascotas | RNF-05 | 2 s o menos, medido y registrado; cierra OBS-05 · D-26: `test_TS05_busquedas.py` en la CI (1,050 mascotas) y `tests/carga/ts05_busquedas.py` en https://dogtor.local; falta medir en la laptop |
| 🔄 | S5-14 | TS-06: Locust con 10 usuarios guardando consultas y cobrando durante 30 min | RNF-05 | 95 % de las operaciones en 2 s o menos y cero errores; cierra OBS-06 · D-26: `preparar_carga` y `tests/carga/locustfile.py`; falta ejecutarla en la laptop |

### F. Compatibilidad y contingencia

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S5-15 | TS-04: flujos principales en Chrome, Edge y tableta; impresión de una receta y un ticket | RNF-02 | Lista de verificación con resultados |
| ⬜ | S5-16 | TS-11: agenda del día imprimible y recaptura al volver la conexión | R07 | La atención continúa y la recaptura no pierde datos |

### G. Pruebas finales y aceptación

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S5-17 | TS-01 completo, TS-09, TS-10 (jornada completa automatizada) y TS-12 | RNF-01, RNF-03, RNF-08, RF-01 a RF-14 | Integración continua en verde |
| ⬜ | S5-18 | Guía de capacitación y guion de TA-09 (jornada simulada) y TA-10 (persona nueva) | RNF-07 | `guion_aceptacion_P5.md` y la guía |
| ⬜ | S5-19 | Aceptación final: TA-09 con el personal y quien imparte la asignatura; TA-10 con una persona nueva en el sistema | Tabla 3.1 | ≥ 4/5; TA-10 en 10 min o menos |

### H. Cierre del proyecto

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S5-20 | Criterios de salida y listas LV finales de todos los módulos | Tabla 4.11 | `evaluacion_P5.md` |
| ⬜ | S5-21 | Restauración final, acta de P5, Tabla 4.20 completa, LV-R final y riesgos | APE | Documentos en `docs/gestion/` |
| ⬜ | S5-22 | Actualización del documento Word con las decisiones D-01 a D-22 y los cambios marcados «Actualizar documento» | — | Documento al día |
| ⬜ | S5-23 | `develop` → `main` y release `v1.0` | — | Línea base final publicada (JECR2005 integra) |

## Avisos del plan

- **TS-08 pide un mes de monitoreo** y el sprint dura dos semanas: se mide en periodo reducido (D-22) y el mes
  completo sigue en operación después de `v1.0`. Conviene dejar el monitor corriendo cuanto antes.
- **TA-09 y TA-10 necesitan otras personas:** TA-09, al personal (o compañeros en esos papeles) y a quien imparte
  la asignatura; TA-10, alguien que nunca haya usado el sistema.
- **Entrega académica del 1 de diciembre:** si el cierre no alcanza, se presenta el estado de ese día y `v1.0`
  queda para el 3 de diciembre.
