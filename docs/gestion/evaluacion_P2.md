# Evaluación de cierre de P2 · Abastecimiento (S2-17 y S2-19)

| Campo | Contenido |
|---|---|
| Nombre del proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P2 · Abastecimiento (RF-11, RF-12; RD-03, RD-05) |
| Equipo | Equipo 1, Gestión de Proyectos de Software |
| Fecha | 18/11/2026 |
| Línea base evaluada | `develop` al 18/11/2026, se publica como `v0.2-P2` (S2-20) |
| Módulo evaluado (LV-03 y LV-04) | INV · Inventario y compras |
| Objetivo | Calificar P2 con las listas LV-01 a LV-04 y decidir su cierre con los criterios de salida de la Tabla 4.11 |
| Responsable de calidad de P2 | Nuñez Hernandez Ricardo (`roles.md`), quien revisa y firma estas listas |

**Control de versionado**

| Versión | Fecha | Responsable | Tipo de cambio (alta, corrección, actualización) |
|---|---|---|---|
| 1.0 | 18/11/2026 | Claude (borrador) · revisión del responsable de calidad de P2 | Alta |

Escala por punto (múltiplos de 10): No existe = 0 · Deficiente = 10–50 · Buen nivel = 60–80 · Excelente = 90–100.
N/A = el punto depende de un caso de un prototipo posterior y no se califica en P2. Los módulos SEG, CAT y AGE
conservan su calificación de P1 (`evaluacion_P1.md`); P2 no los modificó salvo el menú y la Ayuda.

## 1. Criterios de salida (Tabla 4.11) · S2-17

| Criterio | Meta | Resultado en P2 | Cumple |
|---|---|---|---|
| Defectos críticos abiertos | 0 | 0 | Sí |
| Defectos mayores abiertos | ≤ 3 | 0 (DEF-005 cerrado el 17/11) | Sí |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 2 de 2: RD-03 (TU-06, `test_S2_13_RD03_…`) y RD-05 (TU-07 a TU-09, tres CHECK de la base y adelanto de TS-12) | Sí |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % (870 pruebas, corrida 44438931162) | Sí |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 93 % · LV-02 93 % · LV-03-INV 93 % · LV-04-INV 100 %; punto más bajo: 80 % | Sí |
| Calificación del personal | ≥ 4 de 5 | 4.0 (cinco aspectos del acta) | Sí |
| Restauración de un respaldo (RNF-04) | < 120 min | 0.56 s con los datos de P2 (SQL Server 2025) | Sí |

**Decisión:** P2 cumple todos los criterios de salida → **Cerrar** y publicar `v0.2-P2`.

## 2. Tabla 4.20 · Resumen de resultados de P2

| Prototipo | Casos base | Ejecutados | Aprobados | Tasa de aprobación | Críticos abiertos | Mayores abiertos | Cobertura | Calificación del personal | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| P2 | 6 | 6 | 6 | 100 % | 0 | 0 | 96 % | 4.0 | Cerrar |

Casos base de P2 (Tabla 4.17): TU-06 a TU-09, TI-03 y TA-03. Además se adelantó TS-12 (dos descuentos
simultáneos del último lote), que es de P5 y quedó aprobado. Defectos de P2: DEF-005 (Mayor) y DEF-006 (Menor),
ambos en herramientas de base de datos y cerrados con prueba.

## 3. Formato LV-01 · Aseguramiento de calidad

| N.º | Punto a verificar | Evidencia en P2 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Existe un responsable de los procesos de prueba? | Responsable de calidad de P2 nombrado en `roles.md` y en el acta; falta su firma. | 90 | Excelente |
| 2 | ¿Se verifica que las especificaciones estén implementadas? | RF-11, RF-12, RD-03 y RD-05 con casos; cada RD con pruebas que intentan violarla en el servicio y en la base. | 100 | Excelente |
| 3 | ¿Hay control de que se satisfacen las expectativas del cliente? | TA-03 con guion, 7 de 7 pasos sin ayuda, calificación 4/5 y acta de P2; firmas pendientes. | 90 | Excelente |
| 4 | ¿Los defectos se reportan para su corrección? | DEF-005 y DEF-006 registrados con causa raíz, corregidos con prueba y cerrados el mismo día. | 100 | Excelente |
| 5 | ¿Se identifican tipos y características de los defectos? | Gravedad, origen (Datos) y acción preventiva en cada uno. | 90 | Excelente |
| 6 | ¿Se usan estándares para evaluar las pruebas? | ISO/IEC 25010 en LV-03R, PEP 8 con `ruff`, defectos al estilo IEEE 1044. | 90 | Excelente |
| 7 | ¿Los objetivos se alinean con los riesgos del negocio? | **OBS-02 atendida:** los casos de P2 citan su riesgo en la Tabla 4.19 y la matriz se reevaluó (columna P2). | 90 | Excelente |
| | **Promedio de calidad (%)** | 650 / 7 | **92.9** | **Excelente (90)** |

## 4. Formato LV-02 · Estándares de calidad

| N.º | Punto a verificar | Evidencia en P2 | Calificación (%) | Nivel |
|---|---|---|---|---|
| 1 | ¿Módulos y bloques de información definidos? | Inventario (Productos y lotes · Alertas) y Compras (Proveedores · Pedidos · Recibir pedido) con las pestañas de la Tabla 4.8. | 100 | Excelente |
| 2 | ¿Encabezados escritos correctamente? | Título y ruta de cada pantalla nueva con el nombre de la aplicación igual en todas. | 100 | Excelente |
| 3 | ¿Etiquetas claras y representativas? | Las del diccionario: Stock mínimo, Número de lote, Caducidad, Costo unitario, Condiciones de pago. | 90 | Excelente |
| 4 | ¿Colores definidos por el cliente? | **OBS-03 atendida:** el Administrador aprobó la paleta el 18/11/2026 (azul acciones; verde vigente; amarillo por caducar o pendiente; rojo vencido o error). | 100 | Excelente |
| 5 | ¿Fecha, dinero y números con formato adecuado? | Existencias con decimales solo cuando los hay (97.50 mL, 26), importes $3,340.00, fechas d/m/a. | 90 | Excelente |
| 6 | ¿Pantallas homogéneas? | Mismo patrón de lista, ficha y formulario; falta revisarlas en tableta (OBS-04, se mantiene). | 80 | Buen nivel |
| | **Promedio de calidad (%)** | 560 / 6 | **93.3** | **Excelente (90)** |

## 5. Formato LV-03-INV · Funcionalidad modular, Inventario y compras

| N.º | Punto a verificar | Característica | Evidencia en P2 | INV |
|---|---|---|---|---|
| 1 | Vistas con las funciones que el cliente solicitó | Funcionalidad | RF-11 y RF-12 completos; TA-03 sin ayuda | 90 |
| 2 | Existen todas las vistas | Funcionalidad | UI-08, UI-09 y UI-10 de la Tabla 4.6 | 100 |
| 3 | Los datos capturados se almacenan en la base | Confiabilidad | TI-03; el kardex cuadra con las existencias | 100 |
| 4 | Manejo fácil y de acceso rápido | Usabilidad | TA-03 sin ayuda; «Pedir» desde las alertas; TA-10 en P5 (provisional) | 90 |
| 5 | Los campos de despliegue cambian al modificar valores | Funcionalidad | Importe y total del pedido en vivo; existencias y alertas al recibir o ajustar | 90 |
| 6 | Navegación entre módulos con buen desempeño | Eficiencia | Sin medición formal (OBS-05, se mantiene) | 80 |
| 7 | Ventanas que abren y cierran con buen desempeño | Eficiencia | TS-01 abre cada pantalla nueva con cada rol sin errores | 90 |
| 8 | Cancelar descarta lo capturado | Usabilidad | Cada formulario y confirmación tiene Cancelar | 100 |
| 9 | Cerrar sesión termina el acceso | Confiabilidad | Mismo mecanismo de P1 (DEF-003) | 100 |
| 10 | Existe un menú de ayuda | Usabilidad | Ayuda del Administrador con cinco procedimientos y problemas de inventario | 90 |
| 11 | Tiempo de respuesta adecuado | Eficiencia | Rapidez 4/5 en el acta; TS-06 en P5 (OBS-06, se mantiene) | 80 |
| 12 | La información se muestra de inmediato | Eficiencia | TS-05 es de P5 | N/A |
| 13 | Orden de navegación adecuado | Usabilidad | Alerta → Pedir → Recibir → existencias, validado en TA-03 | 90 |
| 14 | Mensajes de error en el lugar adecuado | Usabilidad | «Stock insuficiente», «Capture la caducidad», «Ya está vencido» junto al campo o partida | 90 |
| 15 | Validaciones en el momento adecuado | Confiabilidad | Caducidad, lote, cantidades y motivo antes de escribir; ajustes con confirmación (RI-04) | 100 |
| 16 | El código cumple los estándares | Mantenibilidad | `ruff` en la CI; revisión en cada PR | 100 |
| 17 | Chrome, Edge y tableta | Portabilidad | TS-04 es de P5 | N/A |
| 18 | Impresión en tamaño carta | Portabilidad | Tickets y cortes en P4 | N/A |
| 19 | Se instala y restaura siguiendo la guía | Portabilidad | Restauración con datos de P2 en 0.56 s; la instalación en servidor limpio se probó en P1 | 90 |
| 20 | Reglas de dominio con operaciones simultáneas | Confiabilidad | Adelanto de TS-12: dos descuentos a la vez nunca dejan negativo; TS-12 completo en P5 | 90 |
| 21 | Cada rol accede solo a lo suyo | Funcionalidad | TS-01: Inventario y Compras solo para el Administrador | 100 |
| 22 | Cada módulo se modifica sin afectar a los demás | Mantenibilidad | App `inventario` con sus pruebas; P1 sigue en verde | 100 |
| | **Promedio de calidad (%)** | | 1,770 / 19 puntos evaluados | **93.2** |

### Formato LV-03R · Resumen por módulo y característica (%)

| Módulo | Funcionalidad | Confiabilidad | Eficiencia | Usabilidad | Portabilidad | Mantenibilidad | Promedio del módulo |
|---|---|---|---|---|---|---|---|
| SEG, CAT, AGE (P1) | 96.7 / 96.7 / 95.0 | 100 | 83.3 | 92.0 | 100 | 100 | 94.1 / 94.1 / 93.9 |
| INV, Inventario y compras | 95.0 | 97.5 | 83.3 | 92.0 | 90.0 | 100 | 93.2 |

## 6. Formato LV-04-INV · Funcionalidad modular, codificación

| N.º | Punto a verificar | Casos | Calificación (%) | Nivel |
|---|---|---|---|---|
| 3 | La vigencia de un lote y el stock disponible se calculan con los valores correctos (RD-03, RD-05) | TU-06, TU-07 | 100 | Excelente |
| 4 | El descuento toma el lote que caduca primero y bloquea cantidades mayores al stock (RD-05) | TU-08, TU-09 | 100 | Excelente |
| | **Promedio de calidad (%)** | | **100** | **Excelente** |

## 7. Formato LV-R · Calidad por lista (%)

| Lista de verificación | P1 | P2 |
|---|---|---|
| LV-01 Aseguramiento de calidad | 91.4 | 92.9 |
| LV-02 Estándares de calidad | 90.0 | 93.3 |
| LV-03 Funcionalidad modular | 94.0 | 93.2 (INV) |
| LV-04 Funcionalidad modular, codificación | 100 | 100 (INV) |
| **Calidad global** | **93.9** | **94.8 · Excelente (90)** |

## 8. Seguimiento de las observaciones de las listas

| ID | Origen | Estado en P2 |
|---|---|---|
| OBS-02 | LV-01 punto 7 (P1) | **Atendida:** columna «Riesgo» en la Tabla 4.19 de P2. |
| OBS-03 | LV-02 punto 4 (P1) | **Atendida:** paleta aprobada por el Administrador el 18/11/2026. |
| OBS-04 | LV-02 punto 6 | Se mantiene: revisión en tableta durante P3 (estética). |
| OBS-05 | LV-03 punto 6 | Se mantiene: medir con TI-10 y TI-11 en P3 y P4. |
| OBS-06 | LV-03 punto 11 | Se mantiene: medir con TS-06 en P5. |

Ningún punto quedó en 50 % o menos, así que las listas no generan defectos nuevos.
