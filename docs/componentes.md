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
| Bootstrap 5.3.3 y Bootstrap Icons 1.11.3 | Estilos, iconos y diseño adaptable | MIT | Interfaz | RNF-02, RNF-07 | `templates/base.html`, `static/vendor/` |
| FullCalendar (paquetes estándar) 6.1.15 | Vista de calendario de la agenda | MIT | Agenda y citas | RF-05 | `templates/agenda/calendario.html`, `static/vendor/fullcalendar/` |
| xhtml2pdf 0.2.23 (con ReportLab, html5lib y pypdf) | PDF de receta, ticket y corte de caja en tamaño carta (D-18; sustituye a WeasyPrint) | Apache-2.0 (ReportLab: BSD) | Reportes y documentos | RF-07, RF-13, RNF-02 | `reportes/services.py` (P3) |
| Gunicorn | Servidor de aplicación en producción | MIT | Despliegue | RNF-06 | `Dockerfile` (D-25) |
| Nginx | Proxy inverso con TLS y cabeceras de seguridad | BSD-2-Clause | Despliegue | RNF-01 | `docker/nginx/dogtor.conf` (D-25) |
| pytest, pytest-django | Pruebas de unidad e integración | MIT, BSD-3-Clause | Plan de calidad | Tabla 3.20 | — |
| coverage.py, pytest-cov | Cobertura de pruebas | Apache-2.0, MIT | Plan de calidad | Tabla 3.20 | — |
| Playwright | TS-04: flujos en Chrome, Edge y tableta emulada (D-27) | Apache-2.0 | Plan de calidad | RNF-02 | `tests/carga/ts04_navegadores.py`, `requirements-carga.txt` |
| Locust (con requests) | Prueba de carga TS-06 y medición de búsquedas TS-05 (D-26) | MIT (requests: Apache-2.0) | Plan de calidad | RNF-05 | `tests/carga/`, `requirements-carga.txt` |
| OWASP ZAP | Prueba de seguridad web (TS-02), imagen `ghcr.io/zaproxy/zaproxy:stable` | Apache-2.0 | Plan de calidad | RNF-01 | `docker-compose.yml` (perfil zap) |
| Docker Desktop | Contenedores del entorno con https (D-22, D-25) | Gratuita para uso personal y educativo | Despliegue | RNF-01, RNF-06 | `Dockerfile`, `docker-compose.yml` |
| mkcert | Autoridad y certificado local para https://dogtor.local (D-25) | BSD-3-Clause | Despliegue | RNF-01 | `scripts/preparar_produccion.ps1` |
| pip-audit | Revisión de vulnerabilidades conocidas en las dependencias (R10) | Apache-2.0 | Plan de calidad | R10 | `.github/workflows/ci.yml` |
| Ruff | Formateo y análisis estático del código | MIT | Mantenibilidad | R12 | — |

## Advertencia sobre FullCalendar (R10)

Las vistas por **recurso** (`resourceTimeGrid`, `resourceTimeline`), que muestran una columna por empleado, son
**premium** y requieren licencia comercial. Para no depender de ellas, la "vista de calendario por empleado" de RF-05
se construye con las vistas estándar (`timeGridWeek`/`timeGridDay`, licencia MIT) y un **filtro por empleado**.
Si el equipo decide usar las vistas premium, debe registrarse aquí la licencia elegida antes de integrarlas.

## Recursos estáticos

Para que la interfaz funcione aunque falle internet en el local (R07), Bootstrap, Bootstrap Icons y FullCalendar
están copiados en `static/vendor/` (S1-15) y ninguna plantilla usa un CDN.

| Componente | Versión | Archivos en `static/vendor/` | Licencia incluida |
|---|---|---|---|
| Bootstrap | 5.3.3 | `bootstrap/css/bootstrap.min.css`, `bootstrap/js/bootstrap.bundle.min.js` | `bootstrap/LICENSE` |
| Bootstrap Icons | 1.11.3 | `bootstrap-icons/bootstrap-icons.min.css`, `bootstrap-icons/fonts/*` | `bootstrap-icons/LICENSE` |
| FullCalendar (estándar) | 6.1.15 | `fullcalendar/index.global.min.js`, `fullcalendar/locales/es.global.min.js` | `fullcalendar/LICENSE.md` |

- Los copia `scripts/traer_componentes.sh` desde los paquetes oficiales de npm con versión fija. En GitHub lo ejecuta
  el flujo «Traer componentes» sobre una rama de trabajo y sube los archivos a esa rama.
- `static/vendor/VERSIONES.txt` guarda la huella SHA-256 de cada archivo, para comprobar que nadie los modificó.
- **Para actualizar una versión:** cambiar el número en el script, abrir una rama, dejar que el flujo copie los
  archivos, revisar el PR y correr todas las pruebas antes de integrarlo (apartado 4.6.1).
- `tests/integracion/test_sin_internet.py` falla si una plantilla vuelve a cargar algo de internet.
