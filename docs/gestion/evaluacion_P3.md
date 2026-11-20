# Evaluación de cierre de P3 · Núcleo clínico y estética (S3-19)

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P3 · Núcleo clínico y estética (RF-06 a RF-10; RD-01, RD-07 a RD-09) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | 20/11/2026 |
| Línea base evaluada | `develop` en `a8ce01e` (20/11/2026), se publica como `v0.3-P3` (S3-22) |
| Módulos evaluados (LV-03 y LV-04) | EXP · Expediente clínico (consulta, aplicaciones, recetas y estética) · REC · Recordatorios |
| Objetivo | Calificar P3 con las listas LV-01 a LV-04 y decidir su cierre con los criterios de salida de la Tabla 4.11 |
| Responsable de calidad de P3 | Aguilar Castillo Hugo Enrique (`roles.md`), quien revisa y firma estas listas |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | 20/11/2026 | Claude (borrador) · revisión del responsable de calidad de P3 | Alta |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.
N/A = el punto depende de un caso de un prototipo posterior o no aplica al módulo. Los módulos SEG, CAT, AGE e INV
conservan su calificación de P1 y P2; P3 solo les agregó el menú con contadores, la Ayuda y la protección de la
consulta firmada.

## 1. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado en P3 | Cumple |
|---|---|---|---|
| Defectos críticos abiertos | 0 | 0 | Sí |
| Defectos mayores abiertos | ≤ 3 | 0 (DEF-007 cerrado el 19/11) | Sí |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 4 de 4: RD-01 (TU-05, `test_S3_15_RD01_…`), RD-07 (TU-14 y cinco pruebas contra la base), RD-08 (TU-15 y dos contra la base), RD-09 (TI-04 y `test_S3_15_RD09_…`) | Sí |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (1169 pruebas, corrida 44644945419 sobre `a8ce01e`) | Sí |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 % · LV-02 95 % · LV-03-EXP 93 % · LV-03-REC 93 % · LV-04 100 %; punto más bajo: 80 % | Sí |
| Calificación del personal | ≥ 4 de 5 | 4.0 en los tres roles (Veterinario, Recepcionista y Estilista) | Sí |
| Restauración de un respaldo (RNF-04) | < 120 min | Pendiente (S3-20) | Pendiente |

**Decisión:** P3 cumple los criterios evaluados; se cierra y se publica `v0.3-P3` en cuanto la restauración con los
datos de P3 quede por debajo de 120 minutos.

## 2. Tabla 4.20 · Resumen de resultados de P3

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P3 | 11 | 11 | 11 | 100 % | 0 | 0 | 96 % | 4.0 | Cerrar |

Casos base de P3 (Tabla 4.17): TU-14 a TU-17, TI-04, TI-08, TI-10, TI-11 y TA-04 a TA-06. TS-01 (adelanto de P5)
se amplió con las 10 rutas nuevas de P3 y quedó aprobado. Defecto de P3: DEF-007 (Mayor, Datos), cerrado con prueba.

## 3. Formato LV-01 · Aseguramiento de calidad

| N.º | Punto a verificar | Evidencia en P3 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Existe un responsable de los procesos de prueba? | Responsable de calidad de P3 nombrado en `roles.md` y en el acta; falta su firma. | 90 | Excelente |
| 2 | ¿Se verifica que las especificaciones estén implementadas? | RF-06 a RF-10 y RD-01, RD-07 a RD-09 con casos; cada RD con pruebas que intentan violarla en el servicio y en la base. | 100 | Excelente |
| 3 | ¿Hay control de que se satisfacen las expectativas del cliente? | TA-04 a TA-06 con guion, sin ayuda, en los tres roles; calificación 4/5 y acta de P3; firmas pendientes. | 90 | Excelente |
| 4 | ¿Los defectos se reportan para su corrección? | DEF-007 registrado con causa raíz, corregido con prueba y verificado en la base local el mismo día. | 100 | Excelente |
| 5 | ¿Se identifican tipos y características de los defectos? | Gravedad, origen (Datos) y acción preventiva. | 90 | Excelente |
| 6 | ¿Se usan estándares para evaluar las pruebas? | ISO/IEC 25010 en LV-03R, PEP 8 con `ruff`, defectos al estilo IEEE 1044. | 90 | Excelente |
| 7 | ¿Los objetivos se alinean con los riesgos del negocio? | Los casos de P3 citan su riesgo (R13, R08, R09, R04, R06) y la matriz se reevaluó (columna P3). | 90 | Excelente |
| | **Promedio de calidad (%)** | 650 / 7 | **92.9** | **Excelente (90)** |

## 4. Formato LV-02 · Estándares de calidad

| N.º | Punto a verificar | Evidencia en P3 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Módulos y bloques de información definidos? | Consulta clínica, Estética y Recordatorios con los submenús de la Tabla 4.8; la consulta agrupa datos, aplicaciones y recetas. | 100 | Excelente |
| 2 | ¿Encabezados escritos correctamente? | Título y ruta en cada pantalla nueva. | 100 | Excelente |
| 3 | ¿Etiquetas claras y representativas? | Las del diccionario: Síntomas, Diagnóstico, Próxima fecha, Estado del pelaje y la piel, Hallazgos. | 90 | Excelente |
| 4 | ¿Colores definidos por el cliente? | Paleta aprobada en P2: rojo para alergias, amarillo para avisos de estética, verde para contactado. | 100 | Excelente |
| 5 | ¿Fecha, dinero y números con formato adecuado? | Pesos en kg con 2 decimales, fechas d/m/a, folio R-AAAA-NNNNN. | 90 | Excelente |
| 6 | ¿Pantallas homogéneas? | Mismo patrón en las pantallas nuevas; **OBS-04 atendida:** revisión en tableta correcta (`revision_tableta_P3.md`). | 90 | Excelente |
| | **Promedio de calidad (%)** | 570 / 6 | **95.0** | **Excelente (90)** |

## 5. Formato LV-03 · Funcionalidad modular, hojas EXP y REC

| N.º | Punto a verificar | Característica | Evidencia en P3 | EXP | REC |
|---|---|---|---|---|---|
| 1 | Vistas con las funciones que el cliente solicitó | Funcionalidad | RF-06 a RF-10 completos; TA-04 a TA-06 sin ayuda | 90 | 90 |
| 2 | Existen todas las vistas | Funcionalidad | UI-11 a UI-16 de la Tabla 4.6 | 100 | 100 |
| 3 | Los datos capturados se almacenan en la base | Confiabilidad | TI-04, TI-08, TI-10 y TI-11 contra SQL Server real | 100 | 100 |
| 4 | Manejo fácil y de acceso rápido | Usabilidad | TA-04 a TA-06 sin ayuda, 4/5; TA-10 en P5 (provisional) | 90 | 90 |
| 5 | Los campos de despliegue cambian al modificar valores | Funcionalidad | Lote sugerido al elegir el producto; peso de la mascota al firmar; contadores de avisos y recordatorios que bajan al atender | 90 | 90 |
| 6 | Navegación entre módulos con buen desempeño | Eficiencia | TI-10 (Recordatorios → Agenda) y TI-11 (Estética → Expediente) sin errores; sin medición formal de tiempo (OBS-05) | 80 | 80 |
| 7 | Ventanas que abren y cierran con buen desempeño | Eficiencia | TS-01 abre las 457 combinaciones de ruta y rol sin errores | 90 | 90 |
| 8 | Cancelar descarta lo capturado | Usabilidad | Atender, receta, estética y firma tienen Cancelar o «No, volver»; Recordatorios no captura formularios | 100 | N/A |
| 9 | Cerrar sesión termina el acceso | Confiabilidad | Mismo mecanismo de P1 (DEF-003) | 100 | 100 |
| 10 | Existe un menú de ayuda | Usabilidad | Ayuda de los cuatro roles con los procedimientos y problemas de P3 (S3-14) | 90 | 90 |
| 11 | Tiempo de respuesta adecuado | Eficiencia | Rapidez 4/5 en el acta; TS-06 en P5 (OBS-06) | 80 | 80 |
| 12 | La información se muestra de inmediato | Eficiencia | TS-05 es de P5 | N/A | N/A |
| 13 | Orden de navegación adecuado | Usabilidad | Consultas del día → Atender → Aplicar → Receta → Firmar y Lista del día → Contactar → Agendar, validados en TA-04 y TA-05 | 90 | 90 |
| 14 | Mensajes de error en el lugar adecuado | Usabilidad | «Antes de firmar capture…», «la próxima fecha es obligatoria», «describa el hallazgo» junto al campo | 90 | 90 |
| 15 | Validaciones en el momento adecuado | Confiabilidad | Firma con confirmación (RI-04); la base rechaza cambiar una consulta firmada (D-19); un segundo «Contactado» no cambia nada | 100 | 100 |
| 16 | El código cumple los estándares | Mantenibilidad | `ruff` en la CI; revisión en cada PR | 100 | 100 |
| 17 | Chrome, Edge y tableta | Portabilidad | Revisión en tableta correcta (OBS-04 atendida); TS-04 formal en P5 | 90 | 90 |
| 18 | Impresión en tamaño carta | Portabilidad | PDF de la receta en carta (D-18), comprobado en la prueba de S3-09 | 100 | N/A |
| 19 | Se instala y restaura siguiendo la guía | Portabilidad | Restauración con los datos de P3: **pendiente (S3-20)**; calificación provisional | 90 | 90 |
| 20 | Reglas de dominio con operaciones simultáneas | Confiabilidad | La aplicación usa el descuento con bloqueo (adelanto de TS-12); el resultado del recordatorio bloquea su fila | 90 | 90 |
| 21 | Cada rol accede solo a lo suyo | Funcionalidad | TS-01 y la Tabla 4.9 celda por celda (S3-14) | 100 | 100 |
| 22 | Cada módulo se modifica sin afectar a los demás | Mantenibilidad | Apps `clinico` y `recordatorios` con sus pruebas; P1 y P2 siguen en verde | 100 | 100 |
| | **Promedio de calidad (%)** | | EXP 1,960 / 21 · REC 1,760 / 19 | **93.3** | **92.6** |

### Formato LV-03R · Resumen por módulo y característica (%)

| Módulo | Funcionalidad | Confiabilidad | Eficiencia | Usabilidad | Portabilidad | Mantenibilidad | Promedio del módulo |
|---|---|---|---|---|---|---|---|
| SEG, CAT, AGE (P1) | 96.7 / 96.7 / 95.0 | 100 | 83.3 | 92.0 | 100 | 100 | 94.1 / 94.1 / 93.9 |
| INV (P2) | 95.0 | 97.5 | 83.3 | 92.0 | 90.0 | 100 | 93.2 |
| EXP, Expediente clínico | 95.0 | 97.5 | 83.3 | 92.0 | 93.3 | 100 | 93.3 |
| REC, Recordatorios | 95.0 | 97.5 | 83.3 | 90.0 | 90.0 | 100 | 92.6 |

## 6. Formato LV-04 · Funcionalidad modular, codificación (EXP y REC)

| N.º | Punto a verificar | Módulo | Casos | Calificación (%) | Nivel |
|---|---|---|---|---|---|
| 8 | La consulta firmada queda en solo lectura y la receta solo existe dentro de una consulta abierta (RD-07, RD-08) | EXP | TU-14, TU-15 | 100 | Excelente |
| 9 | La aplicación exige la próxima fecha en vacunas y desparasitantes, y el recordatorio se genera a 3 días (RF-08, RF-09) | EXP, REC | TU-16, TU-17 | 100 | Excelente |
| | **Promedio de calidad (%)** | | | **100** | **Excelente** |

## 7. Formato LV-R · Calidad por lista (%)

| Lista de verificación | P1 | P2 | P3 |
|---|---|---|---|
| LV-01 Aseguramiento de calidad | 91.4 | 92.9 | 92.9 |
| LV-02 Estándares de calidad | 90.0 | 93.3 | 95.0 |
| LV-03 Funcionalidad modular | 94.0 | 93.2 (INV) | 93.0 (EXP y REC, 3,720 / 40) |
| LV-04 Funcionalidad modular, codificación | 100 | 100 (INV) | 100 (EXP y REC) |
| **Calidad global** | **93.9** | **94.8** | **95.2 · Excelente (90)** |

## 8. Seguimiento de las observaciones de las listas

| ID | Origen | Estado en P3 |
|---|---|---|
| OBS-04 | LV-02 punto 6 | **Atendida:** revisión en tableta el 19/11/2026, sin observaciones; la barra superior, el menú del estilista y las casillas se ajustaron para la tableta (S3-14). |
| OBS-05 | LV-03 punto 6 | Se mantiene: TI-10 y TI-11 recorren la navegación entre módulos sin errores, pero sin medir el tiempo; se medirá con TS-05 y TS-06 en P5. |
| OBS-06 | LV-03 punto 11 | Se mantiene: medir con TS-06 en P5. |

Ningún punto quedó en 50 % o menos, así que las listas no generan defectos nuevos.
