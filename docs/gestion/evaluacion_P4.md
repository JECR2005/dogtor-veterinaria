# Evaluación de cierre de P4 · Ventas y caja (S4-20)

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P4 · Ventas y caja (RF-13, RF-14; RD-06, RD-11, RD-12) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | 20/11/2026 |
| Línea base evaluada | `develop` en `9d59244` (20/11/2026), se publica como `v0.4-P4` (S4-23) |
| Módulos evaluados (LV-03 y LV-04) | VEN · Ventas y caja · REP · Reportes y documentos (PDF de receta, ticket y corte) |
| Objetivo | Calificar P4 con las listas LV-01 a LV-04 y decidir su cierre con los criterios de salida de la Tabla 4.11 |
| Responsable de calidad de P4 | Rodríguez Sánchez Nahomi Gianina (`roles.md`), quien revisa y firma estas listas |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | 20/11/2026 | Claude (borrador) · revisión del responsable de calidad de P4 | Alta |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.
N/A = el punto depende de un caso de un prototipo posterior o no aplica al módulo. Los módulos de P1 a P3 conservan su
calificación; P4 solo les agregó la tarjeta «Tickets con saldo» del Inicio, la Ayuda de caja y las protecciones de
la base de D-21.

## 1. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado en P4 | Cumple |
|---|---|---|---|
| Defectos críticos abiertos | 0 | 0 | Sí |
| Defectos mayores abiertos | ≤ 3 | 0 (P4 no tuvo defectos nuevos) | Sí |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 3 de 3: RD-06 (TU-10, TU-11, pagos rechazados y CHECK de la base), RD-11 (TU-12 y disparador), RD-12 (TU-18, TI-07 y CHECK con función) | Sí |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (1322 pruebas, corrida 44809766313 sobre `9d59244`) | Sí |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 % · LV-02 97 % · LV-03-VEN 94 % · LV-03-REP 94 % · LV-04 100 %; punto más bajo: 80 % | Sí |
| Calificación del personal | ≥ 4 de 5 | 4.0 en Recepcionista y Administrador | Sí |
| Restauración de un respaldo (RNF-04) | < 120 min | 0.62 s con los datos de P4 (11.09 MB, SQL Server 2025) | Sí |

**Decisión:** P4 cumple todos los criterios de salida → **Cerrar** y publicar `v0.4-P4`.

## 2. Tabla 4.20 · Resumen de resultados de P4

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P4 | 10 | 10 | 10 | 100 % | 0 | 0 | 96 % | 4.0 | Cerrar |

Casos base de P4 (Tabla 4.17): TU-10, TU-11, TU-12, TU-18, TI-05, TI-06, TI-07, TI-12, TA-07 y TA-08. Se adelantó
TI-09 (P5): cancelar un ticket pagado como Administrador registra la devolución, el reintegro y la bitácora con los
valores previos (`test_TI06_cancelar_venta.py`). TS-01 ya recorre las 10 rutas de Ventas. Sin defectos nuevos.

## 3. Formato LV-01 · Aseguramiento de calidad

| N.º | Punto a verificar | Evidencia en P4 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Existe un responsable de los procesos de prueba? | Responsable de calidad de P4 nombrado en `roles.md` y en el acta; falta su firma. | 90 | Excelente |
| 2 | ¿Se verifica que las especificaciones estén implementadas? | RF-13, RF-14, RD-06, RD-11 y RD-12 con casos; cada RD con pruebas que intentan violarla en el servicio y en la base (D-21). | 100 | Excelente |
| 3 | ¿Hay control de que se satisfacen las expectativas del cliente? | TA-07 y TA-08 con guion, sin ayuda, como Recepcionista y Administrador; 4/5 y acta de P4; firmas pendientes. | 90 | Excelente |
| 4 | ¿Los defectos se reportan para su corrección? | Registro de defectos al día; P4 no tuvo defectos nuevos y los anteriores siguen cerrados. | 100 | Excelente |
| 5 | ¿Se identifican tipos y características de los defectos? | Formato con gravedad, origen y acción preventiva (IEEE 1044) vigente. | 90 | Excelente |
| 6 | ¿Se usan estándares para evaluar las pruebas? | ISO/IEC 25010 en LV-03R, PEP 8 con `ruff`, defectos al estilo IEEE 1044. | 90 | Excelente |
| 7 | ¿Los objetivos se alinean con los riesgos del negocio? | Los casos de P4 citan su riesgo (R08, R11, R06, R04) y la matriz se reevaluó (columna P4). | 90 | Excelente |
| | **Promedio de calidad (%)** | 650 / 7 | **92.9** | **Excelente (90)** |

## 4. Formato LV-02 · Estándares de calidad

| N.º | Punto a verificar | Evidencia en P4 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Módulos y bloques de información definidos? | Ventas y caja con Tickets, Nuevo ticket, Cancelación y Corte de caja (Tabla 4.8); el ticket agrupa líneas, cobro, factura y pagos. | 100 | Excelente |
| 2 | ¿Encabezados escritos correctamente? | Título y ruta en cada pantalla nueva, con el folio del ticket. | 100 | Excelente |
| 3 | ¿Etiquetas claras y representativas? | Las del diccionario: Monto recibido, Cambio, Saldo, Requiere factura, Folio de receta. | 90 | Excelente |
| 4 | ¿Colores definidos por el cliente? | Paleta aprobada en P2: verde Pagada, amarillo Pendiente, gris Cancelada, siempre con texto e icono. | 100 | Excelente |
| 5 | ¿Fecha, dinero y números con formato adecuado? | Importes $1,620.00 en pantalla, PDF y mensajes; folios T-AAAA-NNNNN; cantidades sin decimales cuando son enteras. | 100 | Excelente |
| 6 | ¿Pantallas homogéneas? | Mismo patrón de lista, detalle y confirmación que P1 a P3; tablas adaptables a la tableta. | 90 | Excelente |
| | **Promedio de calidad (%)** | 580 / 6 | **96.7** | **Excelente (90)** |

## 5. Formato LV-03 · Funcionalidad modular, hojas VEN y REP

| N.º | Punto a verificar | Característica | Evidencia en P4 | VEN | REP |
|---|---|---|---|---|---|
| 1 | Vistas con las funciones que el cliente solicitó | Funcionalidad | VEN: RF-13 y RF-14 completos; TA-07 y TA-08 sin ayuda · REP: PDF de receta, ticket y corte | 90 | 90 |
| 2 | Existen todas las vistas | Funcionalidad | UI-17 a UI-19 de la Tabla 4.6 y sus PDF | 100 | 100 |
| 3 | Los datos capturados se almacenan en la base | Confiabilidad | TI-05, TI-06, TI-07 y TI-12 contra SQL Server real | 100 | N/A |
| 4 | Manejo fácil y de acceso rápido | Usabilidad | TA-07 y TA-08 sin ayuda, 4/5; «Por cobrar hoy» arma el ticket con un clic; botón «PDF para imprimir» | 90 | 90 |
| 5 | Los campos de despliegue cambian al modificar valores | Funcionalidad | Importe y total del ticket en vivo; cambio y saldo restante en vivo al cobrar | 100 | N/A |
| 6 | Navegación entre módulos con buen desempeño | Eficiencia | Agenda → Consulta → Por cobrar → Ticket → Corte sin errores (TA-07); sin medición formal de tiempo (OBS-05) | 80 | N/A |
| 7 | Ventanas que abren y cierran con buen desempeño | Eficiencia | TS-01 abre las 520 combinaciones de ruta y rol sin errores, incluidos los PDF | 90 | 90 |
| 8 | Cancelar descarta lo capturado | Usabilidad | Nuevo ticket con «Cancelar»; la cancelación del ticket pide confirmar y tiene «No, volver» | 100 | N/A |
| 9 | Cerrar sesión termina el acceso | Confiabilidad | Mismo mecanismo de P1 (DEF-003); los PDF también piden sesión | 100 | 100 |
| 10 | Existe un menú de ayuda | Usabilidad | Ayuda de Recepción y Administrador con cobrar, cancelar, corte y problemas de caja (S4-15) | 90 | 90 |
| 11 | Tiempo de respuesta adecuado | Eficiencia | Rapidez 4/5 en el acta; TS-06 en P5 (OBS-06) | 80 | 80 |
| 12 | La información se muestra de inmediato | Eficiencia | TS-05 es de P5 | N/A | N/A |
| 13 | Orden de navegación adecuado | Usabilidad | Por cobrar → ticket → pago → factura → corte, validado en TA-07 | 90 | N/A |
| 14 | Mensajes de error en el lugar adecuado | Usabilidad | «Stock insuficiente», «requiere receta», «como máximo el saldo» y «Para facturar…» junto a la línea o el cobro | 90 | N/A |
| 15 | Validaciones en el momento adecuado | Confiabilidad | Ticket todo o nada; cancelación con resumen y confirmación (RI-04); la base protege líneas, pagos y tickets cancelados (D-21) | 100 | N/A |
| 16 | El código cumple los estándares | Mantenibilidad | `ruff` en la CI; revisión en cada PR | 100 | 100 |
| 17 | Chrome, Edge y tableta | Portabilidad | Pantallas nuevas con el mismo diseño adaptable revisado en tableta en P3; tablas que se desplazan en su caja (prueba por plantilla); TS-04 formal en P5 | 90 | 90 |
| 18 | Impresión en tamaño carta | Portabilidad | PDF del ticket y del corte en carta, comprobados en las pruebas (612 × 792 pt) | 100 | 100 |
| 19 | Se instala y restaura siguiendo la guía | Portabilidad | Restauración con los datos de P4 en 0.62 s (S4-21); la instalación en servidor limpio se probó en P1 | 90 | N/A |
| 20 | Reglas de dominio con operaciones simultáneas | Confiabilidad | Folio con reintento, ticket bloqueado al pagar o cancelar y descuento con bloqueo (adelanto de TS-12) | 90 | N/A |
| 21 | Cada rol accede solo a lo suyo | Funcionalidad | TS-01 y `test_S4_15_permisos_y_ayuda.py`: la Recepcionista no cancela tickets con pagos | 100 | 100 |
| 22 | Cada módulo se modifica sin afectar a los demás | Mantenibilidad | App `ventas` con sus pruebas; los PDF solo por `reportes/services.py` (D-18); P1 a P3 siguen en verde | 100 | 100 |
| | **Promedio de calidad (%)** | | VEN 1,970 / 21 · REP 1,130 / 12 | **93.8** | **94.2** |

### Formato LV-03R · Resumen por módulo y característica (%)

| Módulo | Funcionalidad | Confiabilidad | Eficiencia | Usabilidad | Portabilidad | Mantenibilidad | Promedio del módulo |
|---|---|---|---|---|---|---|---|
| SEG, CAT, AGE (P1) | 96.7 / 96.7 / 95.0 | 100 | 83.3 | 92.0 | 100 | 100 | 94.1 / 94.1 / 93.9 |
| INV (P2) | 95.0 | 97.5 | 83.3 | 92.0 | 90.0 | 100 | 93.2 |
| EXP y REC (P3) | 95.0 | 97.5 | 83.3 | 92.0 / 90.0 | 93.3 / 90.0 | 100 | 93.3 / 92.6 |
| VEN, Ventas y caja | 97.5 | 97.5 | 83.3 | 92.0 | 93.3 | 100 | 93.8 |
| REP, Reportes y documentos | 96.7 | 100 | 85.0 | 90.0 | 95.0 | 100 | 94.2 |

## 6. Formato LV-04 · Funcionalidad modular, codificación (VEN)

| N.º | Punto a verificar | Casos | Calificación (%) | Nivel |
|---|---|---|---|---|
| 5 | El pago nunca excede el saldo, calcula el cambio y la venta pasa a Pagada solo con saldo cero (RD-06) | TU-10, TU-11 | 100 | Excelente |
| 6 | Cada línea del ticket conserva el precio vigente al generarse (RD-11) | TU-12 | 100 | Excelente |
| 10 | Un producto con control solo se vende con el folio de una receta válida (RD-12) | TU-18 | 100 | Excelente |
| | **Promedio de calidad (%)** | | **100** | **Excelente** |

## 7. Formato LV-R · Calidad por lista (%)

| Lista de verificación | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| LV-01 Aseguramiento de calidad | 91.4 | 92.9 | 92.9 | 92.9 |
| LV-02 Estándares de calidad | 90.0 | 93.3 | 95.0 | 96.7 |
| LV-03 Funcionalidad modular | 94.0 | 93.2 (INV) | 93.0 (EXP y REC) | 93.9 (VEN y REP, 3,100 / 33) |
| LV-04 Funcionalidad modular, codificación | 100 | 100 (INV) | 100 (EXP y REC) | 100 (VEN) |
| **Calidad global** | **93.9** | **94.8** | **95.2** | **95.9 · Excelente (90)** |

## 8. Seguimiento de las observaciones de las listas

| ID | Origen | Estado en P4 |
|---|---|---|
| OBS-05 | LV-03 punto 6 | Se mantiene: TA-07 recorre Agenda → Consulta → Ventas sin errores, pero sin medir el tiempo; se medirá con TS-05 y TS-06 en P5. |
| OBS-06 | LV-03 punto 11 | Se mantiene: medir con TS-06 en P5. |

Ningún punto quedó en 50 % o menos, así que las listas no generan defectos nuevos.
