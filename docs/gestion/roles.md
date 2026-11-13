# S0-01 · Roles, componentes y suplentes

**Proyecto:** Dogtor: Veterinaria & Petcare · **Equipo 1** · Gestión de Proyectos de Software
**Referencias:** Tablas 3.2, 3.17 y 3.20; procesos APE y DMS de MoProSoft (Tabla 3.19); riesgo R03.

> Asignación propuesta el 13/11/2026. El equipo puede intercambiar roles según las fortalezas de cada quien;
> si lo hace, actualiza este archivo en un pull request antes de iniciar P1.
> Los trabajadores de la clínica (veterinario, estilista, recepcionista, administrador) son **ficticios** y viven
> en los datos de prueba (`python manage.py cargar_datos_prueba`); este archivo trata de los integrantes del equipo.

## Roles de gestión (Tabla 3.17)

| Rol | Responsabilidades | Riesgos a su cargo | Titular | Suplente |
|---|---|---|---|---|
| Líder del proyecto | Plan, reunión semanal, desviación ≤ 10 %, control de cambios (cláusula Séptima), escalamiento de riesgos críticos | R01, R02, R03, R11 | Castillo Ruiz Jesus Enrique | Cisneros Guevara Carlos Daniel |
| Responsable de base de datos | Esquema en SQL Server (`bd/`), vista, índices, respaldos, rendimiento | R05, R14 | Aguilar Castillo Hugo Enrique | Castillo Ruiz Jesus Enrique |
| Responsable de seguridad | RNF-01, RNF-03, RNF-08, OWASP ZAP, secretos, dependencias | R06, R10 | Nuñez Hernandez Ricardo | Aguilar Castillo Hugo Enrique |
| Responsable de pruebas y capacitación | Datos de prueba, Playwright, aceptación, guía de usuario, capacitación | R04 | Rodríguez Sánchez Nahomi Gianina | Nuñez Hernandez Ricardo |
| Desarrollador clínico | Reglas clínicas y su validación (consultas, recetas, aplicaciones) | R13 | Cisneros Guevara Carlos Daniel | Rodríguez Sánchez Nahomi Gianina |
| Responsable de calidad (rota) | Revisión entre pares, defectos, auditoría PQA, Tabla 4.20 y LV-R | R08, R12 | Rota por prototipo (ver abajo) | — |

Regla de suplencia (R03): cada titular respalda a otro integrante, de modo que nadie es suplente de quien lo suple
y cualquier componente puede continuar si un integrante falta.

## Componentes (Tabla 3.2) y prototipo en que se construyen

| Componente / app de Django | Prototipo | Titular | Suplente |
|---|---|---|---|
| Seguridad y acceso (`seguridad`) | P1, P5 | Nuñez Hernandez Ricardo | Aguilar Castillo Hugo Enrique |
| Catálogos (`catalogos`) | P1, P2 | Rodríguez Sánchez Nahomi Gianina | Nuñez Hernandez Ricardo |
| Agenda y citas (`agenda`) | P1 | Castillo Ruiz Jesus Enrique | Cisneros Guevara Carlos Daniel |
| Inventario y compras (`inventario`) | P2 | Aguilar Castillo Hugo Enrique | Castillo Ruiz Jesus Enrique |
| Expediente clínico (`clinico`) | P3 | Cisneros Guevara Carlos Daniel | Rodríguez Sánchez Nahomi Gianina |
| Recordatorios (`recordatorios`) | P3 | Rodríguez Sánchez Nahomi Gianina | Cisneros Guevara Carlos Daniel |
| Reportes y documentos (`reportes`) | P3, P4 | Nuñez Hernandez Ricardo | Rodríguez Sánchez Nahomi Gianina |
| Ventas y caja (`ventas`) | P4 | Castillo Ruiz Jesus Enrique | Aguilar Castillo Hugo Enrique |
| Base de datos SQL Server (`bd/`) | Todos | Aguilar Castillo Hugo Enrique | Castillo Ruiz Jesus Enrique |

## Rotación del responsable de calidad

Regla: en cada prototipo, el responsable de calidad **no** es titular del componente principal de ese prototipo
(apartado 3.2.4), para que nadie revise su propio trabajo.

| Prototipo | Componente principal (titular) | Responsable de calidad |
|---|---|---|
| P1 | Agenda (Castillo), Catálogos (Rodríguez), Seguridad (Nuñez) | Cisneros Guevara Carlos Daniel |
| P2 | Inventario y compras (Aguilar) | Nuñez Hernandez Ricardo |
| P3 | Expediente clínico (Cisneros) | Aguilar Castillo Hugo Enrique |
| P4 | Ventas y caja (Castillo) | Rodríguez Sánchez Nahomi Gianina |
| P5 | Integración y endurecimiento (todos) | Castillo Ruiz Jesus Enrique, con revisión cruzada del equipo |

## Carga por prototipo (para revisar que esté balanceada)

| Integrante | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| Castillo Ruiz Jesus Enrique | Agenda | Suplente BD | — | Ventas | Calidad |
| Aguilar Castillo Hugo Enrique | Esquema y migraciones | Inventario | Calidad | Suplente ventas | Respaldos y rendimiento |
| Nuñez Hernandez Ricardo | Seguridad | Calidad | Reportes (receta PDF) | Reportes (ticket, corte) | Bitácora y ZAP |
| Rodríguez Sánchez Nahomi Gianina | Catálogos | Catálogos (productos) | Recordatorios | Calidad | Aceptación y guía de usuario |
| Cisneros Guevara Carlos Daniel | Calidad | Apoyo inventario | Expediente clínico | Apoyo ventas | Aceptación |

## Conformidad del equipo

Cada integrante confirma su rol aprobando el pull request que integra este archivo en `develop`
(evidencia de APE · Planeación). Si se prefiere firma, imprimir esta página y anexarla al acta.

| Integrante | Conformidad | Fecha |
|---|---|---|
| Castillo Ruiz Jesus Enrique | | |
| Aguilar Castillo Hugo Enrique | | |
| Nuñez Hernandez Ricardo | | |
| Rodríguez Sánchez Nahomi Gianina | | |
| Cisneros Guevara Carlos Daniel | | |
