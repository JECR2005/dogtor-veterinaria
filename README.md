# Dogtor · Sistema de gestión veterinaria

Sistema web de gestión de clientes, citas, expedientes clínicos, inventario y ventas para
**Dogtor: Veterinaria & Petcare** (Tampico, Tamaulipas). Proyecto de la asignatura Gestión de Proyectos de
Software, Equipo 1.

- **Ciclo de vida:** prototipado evolutivo con desarrollo basado en componentes (apartado 3.1), prototipos P1 a P5.
- **Plataforma:** Python 3.12, Django 5.2 LTS, **SQL Server** (2019, 2022 o 2025; Express sirve), Bootstrap 5.
- **Base de datos:** las 26 tablas están programadas en T-SQL en [`bd/`](bd/). Django solo las usa (decisión D-10).
- **Estado:** Sprint 0 (preparación del entorno). Ver la lista de cierre al final.

## Instalación local (S0-22)

Objetivo: cualquier integrante levanta el sistema en menos de 30 minutos siguiendo estos pasos.

### Atajo: equipo nuevo con Windows (dos comandos)

1. **PowerShell como administrador** (clic derecho → Ejecutar como administrador). Instala Git, Python 3.12,
   SQL Server 2022 Express (si no hay ya una instancia), ODBC Driver 18 y SSMS con winget, y clona el repositorio
   en `Documentos\dogtor-veterinaria`. Si el instalador de SQL Server falla con el código 1009 (idioma de Windows
   distinto del formato regional), instálalo a mano en modo Básica y acepta continuar en inglés:

   ```powershell
   irm https://raw.githubusercontent.com/JECR2005/dogtor-veterinaria/develop/scripts/preparar_equipo.ps1 -OutFile $env:TEMP\preparar_equipo.ps1
   powershell -ExecutionPolicy Bypass -File $env:TEMP\preparar_equipo.ps1
   ```

2. **PowerShell normal**, en la carpeta del proyecto. Detecta la instancia (`localhost\SQLEXPRESS` o la
   predeterminada `localhost`) y crea `.venv`, `.env`, la base `Dogtor` con sus 26 tablas,
   las tablas de Django y los datos ficticios, y corre las pruebas de humo:

   ```powershell
   cd "$HOME\Documents\dogtor-veterinaria"
   powershell -ExecutionPolicy Bypass -File scripts\instalar_local.ps1
   ```

Después: `.\.venv\Scripts\python.exe manage.py runserver` y abrir http://127.0.0.1:8000. Los datos de la base
son ficticios: un equipo nuevo empieza con los datos de prueba, no con los del equipo anterior (para llevarlos,
restaurar un respaldo con `scripts/respaldo.py`).

Los pasos manuales equivalentes siguen abajo.

### 1. Requisitos

| Programa | Nota |
|---|---|
| SQL Server 2022 Express o Developer | Gratuitos. Al instalar, elegir **autenticación mixta** si van a usar la cuenta `dogtor_app`; si no, se puede trabajar con la cuenta de Windows. |
| SQL Server Management Studio (SSMS) | Para ver y administrar las tablas. |
| ODBC Driver 18 for SQL Server | Lo usa Django para conectarse. Se descarga del sitio de Microsoft. |
| Python 3.12 o 3.13 | En Windows, marcar "Add python.exe to PATH". |
| Git y Visual Studio Code | Al abrir la carpeta, aceptar las extensiones recomendadas (`.vscode/extensions.json`). |

### 2. Base de datos en SQL Server

Ejecuta los scripts **en este orden**, en SSMS (abrir el archivo y pulsar Ejecutar) o con `sqlcmd`:

| Orden | Script | Conectado a | Qué hace |
|---|---|---|---|
| 1 | `bd/00_crear_base_y_usuario.sql` | `master`, con cuenta administradora | Crea la base `Dogtor` y la cuenta `dogtor_app`. **Antes, cambia la contraseña** en el script. |
| 2 | `bd/01_tablas.sql` | `Dogtor` | Crea las 26 tablas con llaves, restricciones, índices y el disparador de RD-07. |
| 3 | `bd/02_vistas.sql` | `Dogtor` | Crea la vista `vista_stock_disponible` (RD-05). |
| 4 | `bd/03_prueba_esquema.sql` | `Dogtor` | 19 pruebas de estructura, reglas, vista y disparador. Todo se revierte: no deja datos. |
| 5 | `bd/04_prueba_respaldo.sql` | `master` | Respaldo con verificación y restauración cronometrada en una base temporal (RNF-04, una vez por prototipo). |

Con `sqlcmd` (instancia Express con nombre `SQLEXPRESS`, cuenta de Windows):

```bat
sqlcmd -S localhost\SQLEXPRESS -E -C -i bd\00_crear_base_y_usuario.sql
sqlcmd -S localhost\SQLEXPRESS -E -C -I -d Dogtor -i bd\01_tablas.sql
sqlcmd -S localhost\SQLEXPRESS -E -C -I -d Dogtor -i bd\02_vistas.sql
```

Los pasos 2 y 3 también se pueden hacer con `python bd/ejecutar.py` una vez configurado el `.env` (paso 3).
Para empezar de cero en tu computadora: `python bd/ejecutar.py --recrear` (borra y recrea las tablas, también las de Django, y ejecuta `migrate`; solo local) y después `python manage.py cargar_datos_prueba`.

### 3. Proyecto

> **Atajo en Windows (S1-02):** después de clonar, `powershell -ExecutionPolicy Bypass -File scripts\instalar_local.ps1`
> hace los pasos 3, 4 y 5 por ti (Python, ODBC, `.venv`, `.env` con autenticación de Windows, `migrate`,
> datos ficticios y pruebas de humo). Los comandos manuales siguen abajo.


```bash
git clone <url-del-repositorio> dogtor
cd dogtor
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # Linux / macOS: cp .env.example .env
```

Edita `.env`:

| Variable | Valor |
|---|---|
| `DB_HOST` | `localhost\SQLEXPRESS` (Express) o `localhost` (instancia predeterminada) |
| `DB_USUARIO` / `DB_CONTRASENA` | `dogtor_app` y la contraseña del paso 2. Deja `DB_USUARIO` vacío para usar tu cuenta de Windows. |
| `DB_CONFIAR_CERTIFICADO` | `si` en local (el certificado del servidor es autofirmado) |

El archivo `.env` nunca se sube al repositorio.

### 4. Tablas de Django, cuenta inicial y datos ficticios

Django guarda en la misma base sus propias tablas (sesiones, historial de migraciones). Las 26 tablas del
sistema ya existen por el paso 2, así que el orden importa: **primero `bd/`, después `migrate`**.

```bash
python manage.py migrate
python manage.py createsuperuser        # crea también el empleado Administrador (D-05)
python manage.py cargar_datos_prueba    # 50 mascotas ficticias, catálogos y 4 cuentas de prueba
python manage.py runserver
```

Abre http://127.0.0.1:8000/ (inicio) y http://127.0.0.1:8000/salud/ (debe responder `{"estado": "ok"}`).
El sitio de administración del entorno local está en http://127.0.0.1:8000/admin-local/.

> **Solo la primera vez, solo el responsable de base de datos:** antes de `migrate` ejecuta
> `python manage.py makemigrations seguridad catalogos agenda clinico inventario ventas recordatorios`
> y sube las migraciones en un pull request. Como los modelos son `managed = False`, esas migraciones
> no crean tablas: solo registran los modelos para Django. Los demás integrantes ya solo ejecutan `migrate`.

### 5. Pruebas

```bash
pytest                    # todas; crea test_Dogtor y le aplica bd/01 y bd/02
pytest -m unidad          # solo unidad (no usan la base de datos)
pytest --cov              # con cobertura (meta ≥ 60 %, Tabla 3.20)
ruff check .              # estilo y análisis estático
```

Las pruebas necesitan que la cuenta pueda crear bases (`dbcreator`, lo da el script 00 en desarrollo).

## Respaldo y restauración (RNF-04)

```bash
python scripts/respaldo.py respaldar                       # BACKUP + verificación + copia externa + retención 30 días
python scripts/respaldo.py probar --prototipo P1           # restauración cronometrada; se anota en docs/gestion/
python scripts/respaldo.py restaurar ARCHIVO.bak --base NOMBRE
```

- `RESPALDO_DIR` debe ser una carpeta absoluta del equipo de SQL Server con permiso de escritura para el
  servicio (por ejemplo `C:\DogtorRespaldos`).
- La prueba de restauración se ejecuta **una vez por prototipo** y debe tardar menos de 120 minutos.
- SQL Server Express no incluye el Agente SQL. Las tareas diarias se programan con el Programador de tareas
  de Windows (S5-08): en PowerShell **como administrador**, desde la carpeta del proyecto,

```powershell
powershell -ExecutionPolicy Bypass -File scripts\programar_tareas.ps1 -Probar
```

  crea en la carpeta «Dogtor» el **Respaldo diario** (22:00), los **Recordatorios del día** (08:30, lunes a
  sábado), la **Agenda del día** en PDF (08:35, lunes a sábado; TS-11) y el **Monitor de disponibilidad** (cada 5 min de 9:00 a 19:00, lunes a sábado; TS-08). Lo que
  hacen queda en `logs\tareas.log` y `logs\disponibilidad.csv`; `python scripts/monitor.py reporte` arma el
  reporte de TS-08. Con `-Quitar` se eliminan.
- **TS-07 en un servidor limpio** (S5-09, D-24): con Docker Desktop y `RESTAURACION_*` en `.env`,

```powershell
docker compose --env-file .env -f docker/servidor_limpio.yml up -d
python scripts/respaldo.py ts07
docker compose --env-file .env -f docker/servidor_limpio.yml down
```

  respalda la base, la restaura en un SQL Server 2025 nuevo dentro de un contenedor, revisa su integridad y
  compara los registros de cada tabla (`docs/gestion/ts07_restauracion.md`).

## Entorno con https en Docker (S5-12, D-22, D-25)

El «servidor del local» de la Tabla 4.2 corre en Docker Desktop: Nginx con TLS (certificado de mkcert) delante
de Gunicorn, conectado al SQL Server de la laptop con la cuenta `dogtor_web`. Con Docker Desktop abierto, en
PowerShell **como administrador** desde la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\preparar_produccion.ps1
```

Prepara el certificado, el nombre `dogtor.local`, TCP/IP y la autenticación de SQL Server, la cuenta y los
secretos (`docker/produccion.env`, nunca al repositorio) y levanta https://dogtor.local. Después:
`docker compose ps`, `docker compose logs -f web`, `docker compose up -d --build` (tras un `git pull`) y
`docker compose run --rm zap` (TS-02 con OWASP ZAP).

## Estructura (Tabla 4.24)

```
dogtor/
├── bd/              T-SQL: base y cuenta (00), 26 tablas (01), vista (02), borrado local (99), cambios/
├── config/          configuración por entorno (local, test, pruebas, produccion) y rutas
├── seguridad/       usuarios, roles, menú por rol y bitácora            · Seguridad y acceso
├── catalogos/       clientes, mascotas, empleados, servicios, productos · Catálogos
├── agenda/          citas                                               · Agenda y citas
├── clinico/         expediente, consultas, aplicaciones, recetas, estética · Expediente clínico
├── inventario/      lotes, movimientos y pedidos de compra              · Inventario y compras
├── ventas/          tickets, partidas y pagos                           · Ventas y caja
├── recordatorios/   lista diaria de contacto                            · Recordatorios
├── reportes/        PDF de receta, ticket y corte (sin tablas propias)  · Reportes y documentos
├── templates/ static/
├── tests/           unidad, integracion y sistema
├── scripts/         respaldo, creación del backlog y protección de ramas
└── docs/            gestión del proyecto, componentes y decisiones técnicas
```

Cada app separa `models.py` (los modelos que usan las tablas de `bd/`), `services.py` (reglas de negocio)
y `views.py` (pantallas). Las reglas de trabajo del equipo están en [CONTRIBUTING.md](CONTRIBUTING.md).

## Puesta en marcha del repositorio en GitHub (una sola vez, el líder)

```bash
git remote add origin https://github.com/JECR2005/dogtor-veterinaria.git
git push -u origin main develop
# S0-06: regla creada en Settings → Rules → Rulesets («Proteccion main y develop»); scripts/proteger_ramas.sh es la alternativa por API
python scripts/crear_issues.py --repo JECR2005/dogtor-veterinaria --dry-run
python scripts/crear_issues.py --repo JECR2005/dogtor-veterinaria   # S0-02: 34 issues, hitos P1 a P5 (API REST)
```

## Lista de cierre del Sprint 0

| ID | Actividad | Estado |
|---|---|---|
| S0-01 | Roles y suplentes (`docs/gestion/roles.md`) | Hecho (propuesta) · Falta: conformidad del equipo en el PR |
| S0-02 | Backlog de 34 requisitos (`docs/gestion/backlog.csv`, `scripts/crear_issues.py`) | Hecho: 34 issues y 5 hitos en GitHub |
| S0-03 | Plantillas de gestión (`docs/gestion/`) | Hecho |
| S0-04 | Registro de componentes y licencias (`docs/componentes.md`) | Hecho |
| S0-05 | Repositorio con carpetas de código, documentación y pruebas | Hecho: github.com/JECR2005/dogtor-veterinaria |
| S0-06 | Ramas main/develop protegidas | Hecho: regla «Proteccion main y develop» activa (PR + CI «pruebas», 0 aprobaciones, sin force push ni borrado; D-14) |
| S0-07 | Convenciones y plantillas de PR e issues | Hecho |
| S0-08 | `.gitignore` y `.env.example` | Hecho |
| S0-09 | VS Code y ruff comunes | Hecho |
| S0-10 | Dependencias con versiones exactas | Hecho: fijadas con las versiones verificadas por la CI |
| S0-11 | Configuración por entorno | Hecho |
| S0-12 | Ocho apps con models/services/views/urls | Hecho |
| S0-13 | Usuario propio (Tabla 3.38) | Hecho |
| S0-14 | 26 tablas en SQL Server (`bd/01_tablas.sql`), modelos y migraciones | Hecho: 19/19 pruebas en SSMS y migraciones generadas por la CI |
| S0-15 | Índices recomendados | Hecho (en `bd/01_tablas.sql`) |
| S0-16 | Plantilla base con menú por rol | Hecho |
| S0-17 | pytest y cobertura | Hecho |
| S0-18 | Integración continua con SQL Server (`.github/workflows/ci.yml`) | Hecho: en verde, 42/42 pruebas, cobertura 94.6 % |
| S0-19 | Datos ficticios (`cargar_datos_prueba`) | Hecho |
| S0-20 | Pruebas de humo por app | Hecho |
| S0-21 | Respaldo y restauración (`scripts/respaldo.py`, `bd/04_prueba_respaldo.sql`) | Hecho: restauración en 0.52 s, 26/26 tablas (`docs/gestion/registro_restauraciones.md`) |
| S0-22 | README | Hecho |

Al completar la lista: `git tag -a v0.0-S0 -m "Línea base del entorno"`.
