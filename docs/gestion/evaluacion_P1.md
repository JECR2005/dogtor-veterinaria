# Evaluación de cierre de P1 · Núcleo de operación (S1-22 y S1-24)

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P1 · Núcleo de operación (RF-01 a RF-05; RD-01, RD-02, RD-04, RD-10; RNF-01) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | 17/11/2026 |
| Línea base evaluada | `develop` al 17/11/2026, se publica como `v0.1-P1` (S1-25) |
| Módulos evaluados (LV-03 y LV-04) | SEG · CAT · AGE |
| Objetivo | Calificar P1 con las listas LV-01 a LV-04 del Banco de pruebas y decidir su cierre con los criterios de salida de la Tabla 4.11 |
| Responsable de calidad de P1 | Cisneros Guevara Carlos Daniel (`roles.md`), quien revisa y firma estas listas |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | 17/11/2026 | Claude (borrador) · revisión del responsable de calidad de P1 | Alta |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.
N/A = el punto depende de un caso o módulo de un prototipo posterior y no se califica en P1 (apartado 4.5.3.1).
Los puntos con 60–80 % se anotan como observaciones y se revisan en P2 (sección 6).

## 1. Criterios de salida (Tabla 4.11) · S1-22

| Criterio | Meta | Resultado en P1 | Cumple |
|---|---|---|---|
| Defectos críticos abiertos | 0 | 0 | Sí |
| Defectos mayores abiertos | ≤ 3 | 0 (DEF-001 a DEF-003 cerrados el 17/11) | Sí |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 4 de 4: RD-01 (TU-05), RD-02 (TU-01 a TU-03, TA-02), RD-04 (TU-04, TI-02), RD-10 (TI-01) | Sí |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (reporte `coverage.xml` de la CI) | Sí |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 91 % · LV-02 90 % · LV-03 94 % · LV-04 100 %; punto más bajo: 80 % | Sí |
| Calificación del personal | ≥ 4 de 5 | 5.0 (cinco aspectos del acta) | Sí |
| Restauración de un respaldo (RNF-04) | < 120 min | 0.60 s en un servidor limpio (SQL Server 2025) | Sí |

**Decisión:** P1 cumple todos los criterios de salida → **Cerrar** y publicar `v0.1-P1`.

## 2. Tabla 4.20 · Resumen de resultados de P1

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 10 | 10 | 10 | 100 % | 0 | 0 | 96 % | 5.0 | Cerrar |

Casos base de P1 (Tabla 4.17): TU-01 a TU-05, TU-13, TI-01, TI-02, TA-01 y TA-02. Además se adelantó TS-01
(control de acceso por rol), que es de P5 y también quedó aprobado.

## 3. Formato LV-01 · Aseguramiento de calidad

| N.º | Punto a verificar | Evidencia en P1 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Existe al menos un miembro responsable de realizar los procesos de prueba? | Responsable de calidad de P1 nombrado en `roles.md` y en el acta de P1; falta su firma en el acta. | 90 | Excelente |
| 2 | ¿Se verifica que las especificaciones técnicas estén correctamente implementadas? | Cada RF, RD y RNF de P1 tiene caso (Tabla 4.18) y cada RD tiene una prueba que intenta violarla; la CI corre todo en cada PR. | 100 | Excelente |
| 3 | ¿Existe un control para verificar que las expectativas del cliente estén satisfechas? | TA-01 y TA-02 con el guion `guion_aceptacion_P1.md`, calificación 5/5 y acta de P1; firmas pendientes. | 90 | Excelente |
| 4 | ¿Los probadores reportan los defectos al equipo de desarrollo para su corrección? | DEF-001 a DEF-004 registrados, corregidos con prueba y cerrados (`resultados_pruebas.md`). | 100 | Excelente |
| 5 | ¿Existe un control de identificación de los tipos de defectos y sus características? | Cada defecto tiene gravedad (Tabla 4.21), origen (Tabla 4.22) y causa raíz. | 90 | Excelente |
| 6 | ¿Se utilizan estándares para evaluar los diferentes tipos de pruebas? | ISO/IEC 25010 en LV-03R, PEP 8 con `ruff` en la CI, clasificación de defectos al estilo IEEE 1044. | 90 | Excelente |
| 7 | ¿Se lleva un control de los objetivos para que estén alineados con los riesgos del negocio? | La matriz se reevaluó al cierre (`riesgos.md`, columna P1); los casos aún no citan su riesgo en el registro. | 80 | Buen nivel |
| | **Promedio de calidad (%)** | 640 / 7 | **91.4** | **Excelente (90)** |

## 4. Formato LV-02 · Estándares de calidad

| N.º | Punto a verificar | Evidencia en P1 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Están claramente definidos los módulos y los bloques de información? | Menú con Inicio, Agenda, Clientes y Administración según el rol; la ficha agrupa datos del cliente, mascotas y citas. | 100 | Excelente |
| 2 | ¿Están los encabezados escritos correctamente? | Título de pestaña corregido a «Dogtor: Veterinaria & Petcare» en todas las vistas (prueba `test_estandares_LV02.py`). | 100 | Excelente |
| 3 | ¿Están las etiquetas de los campos escritas de forma clara y representativa? | Etiquetas del diccionario de datos; «Prefiere que lo contacten por» se cambió a «Preferencia de contacto». | 90 | Excelente |
| 4 | ¿Las pantallas muestran los colores definidos por el cliente? | Paleta Bootstrap con los colores de estado de la Tabla 4.5; falta la aprobación expresa del Administrador. | 80 | Buen nivel |
| 5 | ¿Los campos de fecha, dinero y numéricos tienen el formato adecuado? | Formato de México: fechas d/m/a, 24 h, `$1,234.50`, duración en h y min (S1-17). | 90 | Excelente |
| 6 | ¿Son homogéneas todas las pantallas? | Mismas zonas en los cuatro roles (barra, ruta, contenido); falta probar en la tableta (TS-04, P5). | 80 | Buen nivel |
| | **Promedio de calidad (%)** | 540 / 6 | **90.0** | **Excelente (90)** |

## 5. Formato LV-03 · Funcionalidad modular (LV-03-SEG, LV-03-CAT, LV-03-AGE)

| N.º | Punto a verificar | Característica | Evidencia en P1 | SEG | CAT | AGE |
|---|---|---|---|---|---|---|
| 1 | Las vistas muestran las funciones que el cliente solicitó | Funcionalidad | RF-01 a RF-05 en pantallas; TA-01 sin ayuda | 90 | 90 | 90 |
| 2 | Existen todas las vistas del sistema | Funcionalidad | Pantallas de P1 de la Tabla 4.6 completas | 100 | 100 | 100 |
| 3 | Los datos capturados se almacenan en la base de datos | Confiabilidad | TI-01, TI-02 y pruebas contra SQL Server real | 100 | 100 | 100 |
| 4 | Manejo fácil y de acceso rápido | Usabilidad | TA-01 sin ayuda y 5/5; TA-10 se mide en P5 (provisional) | 90 | 90 | 90 |
| 5 | Los campos de despliegue cambian al modificar valores | Funcionalidad | Al elegir el servicio cambian la duración mostrada y los empleados que lo prestan; la hora de fin se calcula al guardar, no en pantalla | N/A | N/A | 90 |
| 6 | Navegación entre módulos con buen desempeño | Eficiencia | Sin esperas perceptibles; medición formal con TI-10, TI-11 y TS-06 | 80 | 80 | 80 |
| 7 | Las ventanas abren y cierran con buen desempeño | Eficiencia | TS-01 abre cada pantalla con cada rol sin errores | 90 | 90 | 90 |
| 8 | Cancelar descarta lo capturado | Usabilidad | Cada formulario tiene Cancelar y no guarda nada | 100 | 100 | 100 |
| 9 | Cerrar sesión termina el acceso | Confiabilidad | DEF-003 cerrado: Atrás ya no muestra datos | 100 | 100 | 100 |
| 10 | Existe un menú de ayuda | Usabilidad | DEF-004 cerrado: Ayuda con la guía del rol | 90 | 90 | 90 |
| 11 | Tiempo de respuesta adecuado | Eficiencia | Rapidez 5/5 en el acta; TS-06 con 10 usuarios en P5 (provisional) | 80 | 80 | 80 |
| 12 | La información se muestra de inmediato | Eficiencia | TS-05 (más de 1,000 mascotas) es de P5 | N/A | N/A | N/A |
| 13 | Orden de navegación adecuado | Usabilidad | Flujo de agendar validado por el personal; OBS-01 atendida | 90 | 90 | 90 |
| 14 | Mensajes de error en el lugar adecuado | Usabilidad | «Empalme de horario» y «Fuera de horario laboral» junto al formulario, con qué hacer (TA-02) | 90 | 90 | 90 |
| 15 | Validaciones en el momento adecuado | Confiabilidad | Cédula, aviso de privacidad y contraseña se validan antes de guardar | 100 | 100 | 100 |
| 16 | El código cumple los estándares del lenguaje | Mantenibilidad | `ruff check` y `ruff format --check` en la CI; revisión en cada PR | 100 | 100 | 100 |
| 17 | Funciona en Chrome, Edge y la tableta | Portabilidad | TS-04 es de P5 | N/A | N/A | N/A |
| 18 | Impresión en tamaño carta | Portabilidad | Recetas, tickets y cortes llegan en P3 y P4 | N/A | N/A | N/A |
| 19 | Se instala y restaura en un servidor limpio | Portabilidad | Laptop nueva con SQL Server 2025: instalación con los scripts y restauración en 0.60 s (S1-23) | 100 | 100 | 100 |
| 20 | Reglas de dominio con operaciones simultáneas | Confiabilidad | TS-12 es de P5 | N/A | N/A | N/A |
| 21 | Cada rol accede solo a lo suyo | Funcionalidad | TS-01 (todas las rutas × roles), D-17 y DEF-002 cerrado | 100 | 100 | 100 |
| 22 | Cada módulo se modifica sin afectar a los demás | Mantenibilidad | Una app de Django por componente con sus pruebas | 100 | 100 | 100 |
| | **Promedio de calidad (%)** | | | **94.1** | **94.1** | **93.9** |

Puntos evaluados: 17 en SEG y CAT, 18 en AGE. Promedio de LV-03 en P1: **94.0 % → Excelente (90)**.

### Formato LV-03R · Resumen por módulo y característica (%)

| Módulo | Funcionalidad | Confiabilidad | Eficiencia | Usabilidad | Portabilidad | Mantenibilidad | Promedio del módulo |
|---|---|---|---|---|---|---|---|
| SEG, Seguridad y acceso | 96.7 | 100 | 83.3 | 92.0 | 100 | 100 | 94.1 |
| CAT, Catálogos | 96.7 | 100 | 83.3 | 92.0 | 100 | 100 | 94.1 |
| AGE, Agenda y citas | 95.0 | 100 | 83.3 | 92.0 | 100 | 100 | 93.9 |
| EXP, INV, VEN, REC, REP | — | — | — | — | — | — | Se evalúan en P2 a P4 |
| **Promedio por característica** | **96.1** | **100** | **83.3** | **92.0** | **100** | **100** | **94.0** |

La eficiencia es la característica más baja porque sus mediciones formales (TS-05, TS-06) son de P5.

## 6. Formato LV-04 · Funcionalidad modular, codificación

| N.º | Punto a verificar | Módulo | Casos | Calificación (%) | Nivel |
|---|---|---|---|---|---|
| 1 | La agenda rechaza una cita empalmada o fuera de horario, con valores límite (RD-02) | AGE | TU-01 a TU-03 | 100 | Excelente |
| 2 | Cada servicio se asigna solo al puesto correcto y solo un veterinario con cédula se da de alta (RD-01, RD-04) | CAT | TU-04, TU-05 | 100 | Excelente |
| 7 | La cuenta se bloquea al quinto intento fallido (RNF-01) | SEG | TU-13 | 100 | Excelente |
| 3–6, 8–10 | Lotes, ventas, consultas, recordatorios y recetas | INV, VEN, EXP, REC | TU-06 a TU-18 | N/A | Se califican en P2 a P4 |
| | **Promedio de calidad (%)** | | | **100** | **Excelente** |

## 7. Formato LV-R · Calidad por lista en P1 (%)

| Lista de verificación | Puntos | P1 | Nivel |
|---|---|---|---|
| LV-01 Aseguramiento de calidad | 7 | 91.4 | Excelente |
| LV-02 Estándares de calidad | 6 | 90.0 | Excelente |
| LV-03 Funcionalidad modular | 22 (17–18 evaluados) | 94.0 | Excelente |
| LV-04 Funcionalidad modular, codificación | 10 (3 evaluados) | 100 | Excelente |
| **Calidad global** | | **93.9** | **Excelente (90)** |

## 8. Observaciones de las listas (puntos con 60–80 %, se revisan en P2)

| ID | Lista y punto | Calificación | Observación | Acción propuesta |
|---|---|---|---|---|
| OBS-02 | LV-01 punto 7 | 80 | Los casos no citan su riesgo en el registro de ejecución. | Agregar la columna «Riesgo» al registro de casos de P2. |
| OBS-03 | LV-02 punto 4 | 80 | La paleta no tiene la aprobación expresa del Administrador. | Revisarla con el Administrador en la aceptación de P2. |
| OBS-04 | LV-02 punto 6 | 80 | Falta probar las pantallas en la tableta de la estética. | Adelantar una revisión en tableta durante P3 (estética). |
| OBS-05 | LV-03 punto 6 | 80 | Sin medición formal del tiempo de navegación entre módulos. | Medir con TI-10 y TI-11 en P3 y P4. |
| OBS-06 | LV-03 punto 11 | 80 | El tiempo de respuesta solo se calificó por percepción. | Medir con TS-06 (10 usuarios) en P5. |

Ningún punto quedó en 50 % o menos, así que las listas no generan defectos nuevos (apartado 4.5.3.3).
