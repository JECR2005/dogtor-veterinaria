# S0-01 · Roles, componentes y suplentes

**Proyecto:** Dogtor: Veterinaria & Petcare · **Equipo 1** · Gestión de Proyectos de Software
**Referencias:** Tablas 3.2, 3.17 y 3.20; procesos APE y DMS de MoProSoft (Tabla 3.19); riesgo R03.

> El equipo llena la columna **Titular** y **Suplente** en la reunión de arranque y firma al final.
> La asignación de componentes por rol es una propuesta; ajústenla a las fortalezas de cada integrante.

## Integrantes

| Integrante | Matrícula |
|---|---|
| Castillo Ruiz Jesus Enrique | 23070410 |
| Aguilar Castillo Hugo Enrique | (pendiente) |
| Nuñez Hernandez Ricardo | (pendiente) |
| Cisneros Guevara Carlos Daniel | 23070039 |
| Rodríguez Sánchez Nahomi Gianina | 22070308 |

## Roles de gestión (Tabla 3.17)

| Rol | Responsabilidades | Riesgos a su cargo | Titular | Suplente |
|---|---|---|---|---|
| Líder del proyecto | Plan, reunión semanal, desviación ≤ 10 %, control de cambios (cláusula Séptima), escalamiento de riesgos críticos | R01, R02, R03, R11 | | |
| Responsable de base de datos | Modelo de 26 tablas, vistas, índices, respaldos, rendimiento | R05, R14 | | |
| Responsable de seguridad | RNF-01, RNF-03, RNF-08, OWASP ZAP, secretos, dependencias | R06, R10 | | |
| Responsable de pruebas y capacitación | Datos de prueba, Playwright, aceptación, guía de usuario, capacitación | R04 | | |
| Desarrollador clínico | Reglas clínicas y validación con el veterinario | R13 | | |
| Responsable de calidad (rota) | Revisión entre pares, defectos, auditoría PQA, Tabla 4.20 y LV-R | R08, R12 | Rota por prototipo (ver abajo) | |

## Componentes (Tabla 3.2) y prototipo en que se construyen

| Componente / app de Django | Prototipo | Rol propuesto | Titular | Suplente |
|---|---|---|---|---|
| Seguridad y acceso (`seguridad`) | P1, P5 | Responsable de seguridad | | |
| Catálogos (`catalogos`) | P1, P2 | Responsable de pruebas y capacitación | | |
| Agenda y citas (`agenda`) | P1 | Líder del proyecto | | |
| Inventario y compras (`inventario`) | P2 | Responsable de base de datos | | |
| Expediente clínico (`clinico`) | P3 | Desarrollador clínico | | |
| Recordatorios (`recordatorios`) | P3 | Responsable de pruebas y capacitación | | |
| Reportes y documentos (`reportes`) | P3, P4 | Responsable de seguridad | | |
| Ventas y caja (`ventas`) | P4 | Líder del proyecto | | |

## Rotación del responsable de calidad

Regla: en cada prototipo, el responsable de calidad **no** puede ser titular del componente principal de ese prototipo (apartado 3.2.4).

| Prototipo | Componente principal | Responsable de calidad |
|---|---|---|
| P1 | Agenda y citas, Catálogos, Seguridad | |
| P2 | Inventario y compras | |
| P3 | Expediente clínico | |
| P4 | Ventas y caja | |
| P5 | Integración y endurecimiento | |

## Firma de conformidad

| Integrante | Firma | Fecha |
|---|---|---|
| | | |
| | | |
| | | |
| | | |
| | | |
