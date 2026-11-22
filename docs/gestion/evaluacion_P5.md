# Evaluación de cierre de P5 · Integración y endurecimiento (S5-20)

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P5 · Integración y endurecimiento (RNF-02 a RNF-08 y cierre de RNF-01) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | 21/11/2026 (versión 1.0; la 1.1 agrega TA-09, TA-10 y el cierre de TS-08) |
| Línea base evaluada | `develop` con el bloque G (`2076d92`, PR #98); al cerrar se publica `v1.0` (S5-23) |
| Módulos evaluados (LV-03 y LV-04) | **Evaluación final de los ocho módulos**: SEG · CAT · AGE · EXP · INV · VEN · REC · REP |
| Objetivo | Calificar el sistema completo con las listas LV-01 a LV-04 y decidir el cierre de P5 y del proyecto con los criterios de salida de la Tabla 4.11 |
| Responsable de calidad de P5 | Castillo Ruiz Jesus Enrique, con revisión cruzada del equipo (`roles.md`) |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | 21/11/2026 | Claude (borrador) · revisión del responsable de calidad de P5 | Alta |
| 1.1 | ____/____/2026 | | Actualización con TA-09, TA-10 y el reporte final de TS-08 |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.
N/A = el punto no aplica al módulo. En P5 se califican **todos los módulos de nuevo**, porque los casos de sistema
(TS-01 a TS-12) dan la evidencia que en P1 a P4 quedó provisional: eficiencia (TS-05, TS-06), compatibilidad e
impresión (TS-04), instalación y restauración en un servidor limpio (TS-07) y concurrencia (TS-12).

## 1. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado en P5 | Cumple |
|---|---|---|---|
| Defectos críticos abiertos | 0 | 0 (DEF-008, encontrado por TS-10, se corrigió el mismo día con prueba) | Sí |
| Defectos mayores abiertos | ≤ 3 | 0 | Sí |
| Reglas RD del sistema con prueba que intenta violarlas | 100 % | 12 de 12; en P5, TS-12 completa RD-05 con un ticket y una aplicación simultáneos | Sí |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (1,465 pruebas, corrida 44972739734 sobre `2076d92`) | Sí |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 92.9 % · LV-02 96.7 % · LV-03 96.1 % (ocho módulos) · LV-04 100 %; punto más bajo: 80 % | Sí |
| Calificación del personal | ≥ 4 de 5 | Pendiente: TA-09 y TA-10 (S5-19) | Pendiente |
| Restauración de un respaldo (RNF-04) | < 120 min | 1.02 s en un **servidor limpio** con conteos iguales en 33 de 33 tablas (TS-07) | Sí |

Criterio de validación de P5 (Tabla 3.1):

| Criterio | Resultado | Cumple |
|---|---|---|
| El sistema supera las pruebas de aceptación | TA-09 y TA-10 pendientes (S5-19); su ensayo automático TS-10 pasa | Pendiente |
| Se restaura un respaldo en menos de 2 horas | 1.02 s en el servidor limpio de Docker (TS-07) | Sí |
| 10 usuarios simultáneos operan sin errores | TS-06: 14,626 operaciones en 30 min, 0 errores, 99.73 % en ≤ 2 s | Sí |

**Decisión provisional:** P5 cumple todos los criterios que no dependen de las personas. Se **cierra** y se publica
`v1.0` si TA-09 y TA-10 se aprueban con un promedio de al menos 4 de 5 y TA-10 en 10 minutos o menos.

## 2. Tabla 4.20 · Resumen de resultados de P5

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P5 | 15 | 12 (+ TS-08 en curso) | 12 | 100 % de lo ejecutado | 0 | 0 | 96 % | Pendiente | Pendiente de S5-19 |

Casos base de P5 (Tabla 4.17): TI-09, TS-01 a TS-12, TA-09 y TA-10. Ejecutados y aprobados: TI-09, TS-01 a TS-07 y
TS-09 a TS-12. TS-08 tiene un corte parcial sin caídas (`disponibilidad_TS08.md`) y se cierra con el reporte
final. TA-09 y TA-10 se ejecutan con el personal (`guion_aceptacion_P5.md`).

## 3. Formato LV-01 · Aseguramiento de calidad

| N.º | Punto a verificar | Evidencia en P5 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Existe un responsable de los procesos de prueba? | Responsable de calidad de P5 nombrado en `roles.md` y en el plan; falta su firma. | 90 | Excelente |
| 2 | ¿Se verifica que las especificaciones estén implementadas? | Los 8 RNF tienen su caso de sistema (TS-01 a TS-12) con resultado; la trazabilidad de la Tabla 4.18 queda al 100 % con casos ejecutados. | 100 | Excelente |
| 3 | ¿Hay control de que se satisfacen las expectativas del cliente? | Guion de TA-09 y TA-10 y guía de capacitación listos; la aceptación con el personal está pendiente (S5-19). **Provisional.** | 80 | Buen nivel |
| 4 | ¿Los defectos se reportan para su corrección? | DEF-008 registrado con causa raíz, corregido con prueba el mismo día; los ocho defectos del proyecto están cerrados. | 100 | Excelente |
| 5 | ¿Se identifican tipos y características de los defectos? | Gravedad, origen y acción preventiva en cada defecto (IEEE 1044). | 90 | Excelente |
| 6 | ¿Se usan estándares para evaluar las pruebas? | ISO/IEC 25010 en LV-03R, IEEE 1044, PEP 8 con `ruff`, OWASP ZAP (línea base), la lista de despliegue de Django (`check --deploy`) y `pip-audit`. | 100 | Excelente |
| 7 | ¿Los objetivos se alinean con los riesgos del negocio? | Cada caso de sistema cita su riesgo (R05, R06, R07, R08, R14, R15) y la matriz se reevaluó (columna P5). | 90 | Excelente |
| | **Promedio de calidad (%)** | 650 / 7 | **92.9** | **Excelente (90)** |

## 4. Formato LV-02 · Estándares de calidad

| N.º | Punto a verificar | Evidencia en P5 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Módulos y bloques de información definidos? | Bitácora con Consultar y Exportar (Tabla 4.8); la corrección de una consulta firmada dentro de la consulta. | 100 | Excelente |
| 2 | ¿Encabezados escritos correctamente? | Título y ruta en la Bitácora, la corrección y el PDF de la agenda. | 100 | Excelente |
| 3 | ¿Etiquetas claras y representativas? | Las del diccionario: Desde, Hasta, Usuario, Acción, Motivo de la corrección, Valores previos. | 90 | Excelente |
| 4 | ¿Colores definidos por el cliente? | Paleta aprobada en P2; la corrección usa el amarillo de advertencia con texto e icono. | 100 | Excelente |
| 5 | ¿Fecha, dinero y números con formato adecuado? | Importes y fechas igual que en P4; DEF-008: los números de registro ya no llevan separador de miles en direcciones y campos. | 90 | Excelente |
| 6 | ¿Pantallas homogéneas? | TS-04: 14 de 14 pasos en Chrome, Edge y la tableta, sin desbordes. | 100 | Excelente |
| | **Promedio de calidad (%)** | 580 / 6 | **96.7** | **Excelente (90)** |

## 5. Formato LV-03 · Funcionalidad modular, evaluación final de los ocho módulos

| N.º | Punto a verificar | Característica | Evidencia en P5 | SEG | CAT | AGE | EXP | INV | VEN | REC | REP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Vistas con las funciones que el cliente solicitó | Funcionalidad | RF-01 a RF-14 y UI-20 Bitácora; TS-10 recorre la jornada completa; TA-09 pendiente | 90 | 90 | 90 | 90 | 90 | 90 | 90 | 90 |
| 2 | Existen todas las vistas | Funcionalidad | UI-01 a UI-20 de la Tabla 4.6 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 3 | Los datos capturados se almacenan en la base | Confiabilidad | TS-10: el kardex de cada lote cuadra y el corte coincide con lo vendido; TS-07: 33 de 33 tablas íntegras | 100 | 100 | 100 | 100 | 100 | 100 | 100 | N/A |
| 4 | Manejo fácil y de acceso rápido | Usabilidad | Aceptación sin ayuda en P1 a P4 (4/5 o 5/5); TA-10 pendiente (**provisional**) | 90 | 90 | 90 | 90 | 90 | 90 | 90 | 90 |
| 5 | Los campos de despliegue cambian al modificar valores | Funcionalidad | Igual que en P1 a P4 | N/A | N/A | 90 | 90 | 90 | 100 | 90 | N/A |
| 6 | Navegación entre módulos con buen desempeño | Eficiencia | **OBS-05 cerrada:** TS-06 guarda consultas y cobra con 10 usuarios a la vez (percentil 95 de 200 ms) y TS-10 recorre los ocho módulos sin errores | 90 | 90 | 90 | 90 | 90 | 90 | 90 | N/A |
| 7 | Ventanas que abren y cierran con buen desempeño | Eficiencia | TS-01: 560 combinaciones de ruta y rol sin errores; TS-04 en tres equipos | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 8 | Cancelar descarta lo capturado | Usabilidad | Igual que en P1 a P4; la corrección tiene Cancelar | 100 | 100 | 100 | 100 | 100 | 100 | N/A | N/A |
| 9 | Cerrar sesión termina el acceso | Confiabilidad | DEF-003; en https las cookies son seguras y de solo servidor (TS-03) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 10 | Existe un menú de ayuda | Usabilidad | Ayuda de los cuatro roles con contingencia (S5-16) y la guía de capacitación (S5-18) | 90 | 90 | 90 | 90 | 90 | 90 | 90 | 90 |
| 11 | Tiempo de respuesta adecuado | Eficiencia | **OBS-06 cerrada:** TS-06 con 99.73 % en ≤ 2 s y 0 errores; quedan pausas aisladas del equipo (0.27 %, R14) | 90 | 90 | 90 | 90 | 90 | 90 | 90 | 90 |
| 12 | La información se muestra de inmediato | Eficiencia | TS-05 con 1,200 mascotas: búsqueda más lenta en 210 ms (clientes, mascotas, productos y tickets) | N/A | 100 | N/A | N/A | 100 | 100 | N/A | N/A |
| 13 | Orden de navegación adecuado | Usabilidad | Validado en TA-01 a TA-08; TS-10 sigue el orden de la jornada | 90 | 90 | 90 | 90 | 90 | 90 | 90 | N/A |
| 14 | Mensajes de error en el lugar adecuado | Usabilidad | Igual que en P1 a P4; la corrección exige el motivo junto al campo | 90 | 90 | 90 | 90 | 90 | 90 | 90 | N/A |
| 15 | Validaciones en el momento adecuado | Confiabilidad | TS-02: ninguna entrada maliciosa altera la base ni se ejecuta (ZAP: 0 altos) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | N/A |
| 16 | El código cumple los estándares | Mantenibilidad | `ruff` en la CI; revisión en cada PR | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 17 | Chrome, Edge y tableta | Portabilidad | TS-04: 14 de 14 pasos en Chrome, Edge y la Galaxy Tab S4 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 18 | Impresión en tamaño carta | Portabilidad | TS-04: receta, ticket, corte y agenda en carta | N/A | N/A | 100 | 100 | N/A | 100 | N/A | 100 |
| 19 | Se instala y restaura siguiendo la guía | Portabilidad | TS-07 en un servidor limpio (1.02 s) y el entorno https levantado con `preparar_produccion.ps1` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | N/A |
| 20 | Reglas de dominio con operaciones simultáneas | Confiabilidad | TS-12 completo: ticket contra aplicación de la última pieza; la agenda bloquea al empleado y a la mascota al agendar | N/A | N/A | 90 | 100 | 100 | 100 | 90 | N/A |
| 21 | Cada rol accede solo a lo suyo | Funcionalidad | TS-01 completo: las pantallas de P1 a P5 con los cuatro roles | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| 22 | Cada módulo se modifica sin afectar a los demás | Mantenibilidad | Una app por componente con sus pruebas; 1,465 pruebas en verde | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| | **Promedio de calidad (%)** | | | **96.1** | **96.3** | **95.7** | **96.2** | **96.2** | **96.8** | **95.3** | **96.7** |

Puntos evaluados: SEG 18, CAT 19, AGE 21, EXP 21, INV 21, VEN 22, REC 19, REP 12 (153 en total, 14,710 puntos).
Promedio de LV-03 en P5: **96.1 % → Excelente (90)**.

### Formato LV-03R · Resumen por módulo y característica (%)

| Módulo | Funcionalidad | Confiabilidad | Eficiencia | Usabilidad | Portabilidad | Mantenibilidad | Promedio del módulo |
|---|---|---|---|---|---|---|---|
| SEG, Seguridad, acceso y bitácora | 96.7 | 100 | 93.3 | 92.0 | 100 | 100 | 96.1 |
| CAT, Catálogos | 96.7 | 100 | 95.0 | 92.0 | 100 | 100 | 96.3 |
| AGE, Agenda y citas | 95.0 | 97.5 | 93.3 | 92.0 | 100 | 100 | 95.7 |
| EXP, Expediente y estética | 95.0 | 100 | 93.3 | 92.0 | 100 | 100 | 96.2 |
| INV, Inventario y compras | 95.0 | 100 | 95.0 | 92.0 | 100 | 100 | 96.2 |
| VEN, Ventas y caja | 97.5 | 100 | 95.0 | 92.0 | 100 | 100 | 96.8 |
| REC, Recordatorios | 95.0 | 97.5 | 93.3 | 90.0 | 100 | 100 | 95.3 |
| REP, Reportes y documentos | 96.7 | 100 | 95.0 | 90.0 | 100 | 100 | 96.7 |

La eficiencia subió de 83 % (P1 a P4) a 93–95 % con las mediciones de TS-05 y TS-06; la usabilidad es ahora la
característica más baja porque TA-09 y TA-10 todavía no se ejecutan.

## 6. Formato LV-04 · Funcionalidad modular, codificación (final)

| N.º | Punto a verificar | Módulo | Casos | Calificación (%) | Nivel |
|---|---|---|---|---|---|
| 1 | La agenda rechaza una cita empalmada o fuera de horario, con valores límite (RD-02) | AGE | TU-01 a TU-03 | 100 | Excelente |
| 2 | Servicio solo al puesto correcto; veterinario solo con cédula (RD-01, RD-04) | CAT | TU-04, TU-05 | 100 | Excelente |
| 3 | Vigencia del lote y stock disponible (RD-03, RD-05) | INV | TU-06, TU-07 | 100 | Excelente |
| 4 | Descuento del lote que caduca primero, sin exceder el stock (RD-05) | INV | TU-08, TU-09, TS-12 | 100 | Excelente |
| 5 | Pago sin exceder el saldo, cambio y cierre con saldo cero (RD-06) | VEN | TU-10, TU-11 | 100 | Excelente |
| 6 | Precio vigente fijo en cada línea (RD-11) | VEN | TU-12 | 100 | Excelente |
| 7 | Bloqueo de la cuenta al quinto intento (RNF-01) | SEG | TU-13 | 100 | Excelente |
| 8 | Consulta firmada de solo lectura y receta solo en consulta abierta (RD-07, RD-08) | EXP | TU-14, TU-15 | 100 | Excelente |
| 9 | Próxima fecha obligatoria en vacunas y desparasitantes y recordatorio a 3 días (RF-08, RF-09) | EXP, REC | TU-16, TU-17 | 100 | Excelente |
| 10 | Medicamento con control solo con folio de receta válida (RD-12) | VEN | TU-18 | 100 | Excelente |
| | **Promedio de calidad (%)** | | | **100** | **Excelente** |

## 7. Formato LV-R · Calidad por lista (%)

| Lista de verificación | P1 | P2 | P3 | P4 | P5 (final) |
|---|---|---|---|---|---|
| LV-01 Aseguramiento de calidad | 91.4 | 92.9 | 92.9 | 92.9 | 92.9 |
| LV-02 Estándares de calidad | 90.0 | 93.3 | 95.0 | 96.7 | 96.7 |
| LV-03 Funcionalidad modular | 94.0 | 93.2 (INV) | 93.0 (EXP y REC) | 93.9 (VEN y REP) | 96.1 (ocho módulos, 14,710 / 153) |
| LV-04 Funcionalidad modular, codificación | 100 | 100 (INV) | 100 (EXP y REC) | 100 (VEN) | 100 (10 de 10) |
| **Calidad global** | **93.9** | **94.8** | **95.2** | **95.9** | **96.4 · Excelente (90)** |

## 8. Seguimiento de las observaciones de las listas

| ID | Origen | Estado en P5 |
|---|---|---|
| OBS-05 | LV-03 punto 6 | **Cerrada (S5-13 y S5-14):** TS-05 midió las búsquedas con 1,200 mascotas (máximo 210 ms) y TS-06 la operación entre Consulta y Ventas con 10 usuarios (percentil 95 de 200 ms). |
| OBS-06 | LV-03 punto 11 | **Cerrada (S5-14):** TS-06 con 14,626 operaciones en 30 min, 0 errores y 99.73 % en ≤ 2 s. Las pausas aisladas se anotaron en R14. |

Ningún punto quedó en 50 % o menos, así que las listas no generan defectos nuevos. Los puntos provisionales (LV-01
punto 3 y LV-03 puntos 1 y 4) se recalifican en la versión 1.1 con el resultado de TA-09 y TA-10.
