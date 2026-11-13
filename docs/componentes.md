# S0-04 · Registro de componentes de terceros y licencias

Área **SAM** de CMMI (Tabla 3.18) y mitigación de **R10** (Tabla 3.17): componentes con licencia clara y
comunidad activa, encapsulados tras una interfaz propia. Las versiones exactas se fijan en
`requirements.txt`; este registro se actualiza en el mismo pull request que agregue o actualice una dependencia.

| Componente | Uso en Dogtor | Licencia | Componente (Tabla 3.2) | Requisitos | Encapsulado en |
|---|---|---|---|---|---|
| Django (serie 5.2 LTS) | Framework web, ORM, autenticación, CSRF, migraciones | BSD-3-Clause | Todos | RNF-01 | — |
| SQL Server 2022 Express / Developer | Gestor de base de datos (D-09) | Licencia de Microsoft, gratuita. Express: hasta 10 GB por base y sin Agente SQL; Developer: solo desarrollo y pruebas | Todos | RD-05, RD-06, RNF-04, RNF-05 | Scripts de `bd/` |
| mssql-django | Conector oficial de Django para SQL Server | BSD-3-Clause | Todos | — | ORM de Django |
| pyodbc | Controlador ODBC para Python (lo instala mssql-django; lo usa `scripts/respaldo.py`) | MIT | Todos | RNF-04 | — |
| Microsoft ODBC Driver 18 for SQL Server | Controlador del sistema operativo | Licencia de Microsoft, gratuita | Todos | RNF-01 (conexión cifrada) | — |
| SQL Server Management Studio | Administración y consulta de la base | Licencia de Microsoft, gratuita | Base de datos | — | — |
| python-dotenv | Leer variables de entorno desde `.env` en desarrollo | BSD-3-Clause | Configuración | RNF-01 | `config/settings/base.py` |
| Bootstrap 5 | Estilos y diseño adaptable | MIT | Interfaz | RNF-02, RNF-07 | `templates/base.html` |
| FullCalendar (paquetes estándar) | Vista de calendario de la agenda | MIT | Agenda y citas | RF-05 | `agenda/` (P1) |
| WeasyPrint | PDF de receta, ticket y corte de caja | BSD-3-Clause | Reportes y documentos | RF-07, RF-13, RNF-02 | `reportes/services.py` (P3) |
| Gunicorn | Servidor de aplicación en producción | MIT | Despliegue | RNF-06 | — |
| Nginx | Proxy inverso con TLS | BSD-2-Clause | Despliegue | RNF-01 | — |
| pytest, pytest-django | Pruebas de unidad e integración | MIT, BSD-3-Clause | Plan de calidad | Tabla 3.20 | — |
| coverage.py, pytest-cov | Cobertura de pruebas | Apache-2.0, MIT | Plan de calidad | Tabla 3.20 | — |
| Playwright | Pruebas de aceptación en navegador | Apache-2.0 | Plan de calidad | RNF-02 | — (P5) |
| Locust | Prueba de carga | MIT | Plan de calidad | RNF-05 | — (P5) |
| OWASP ZAP | Prueba de seguridad web | Apache-2.0 | Plan de calidad | RNF-01 | — (P5) |
| Ruff | Formateo y análisis estático del código | MIT | Mantenibilidad | R12 | — |

## Advertencia sobre FullCalendar (R10)

Las vistas por **recurso** (`resourceTimeGrid`, `resourceTimeline`), que muestran una columna por empleado, son
**premium** y requieren licencia comercial. Para no depender de ellas, la "vista de calendario por empleado" de RF-05
se construye con las vistas estándar (`timeGridWeek`/`timeGridDay`, licencia MIT) y un **filtro por empleado**.
Si el equipo decide usar las vistas premium, debe registrarse aquí la licencia elegida antes de integrarlas.

## Recursos estáticos

Para que la interfaz funcione aunque falle internet en el local (R07), en P1 los archivos de Bootstrap y
FullCalendar se copian a `static/vendor/` en lugar de cargarse desde un CDN. Mientras tanto, `base.html` usa el CDN.
