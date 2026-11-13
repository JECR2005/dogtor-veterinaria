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

Con `sqlcmd` (instancia Express con nombre `SQLEXPRESS`, cuenta de Windows):

```bat
sqlcmd -S localhost\SQLEXPRESS -E -C -i bd\00_crear_base_y_usuario.sql
sqlcmd -S localhost\SQLEXPRESS -E -C -I -d Dogtor -i bd\01_tablas.sql
sqlcmd -S localhost\SQLEXPRESS -E -C -I -d Dogtor -i bd\02_vistas.sql
```

Los pasos 2 y 3 también se pueden hacer con `python bd/ejecutar.py` una vez configurado el `.env` (paso 3).
Para empezar de cero en tu computadora: `python bd/ejecutar.py --recrear` (borra y recrea; solo local).

### 3. Proyecto

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
- SQL Server Express no incluye el Agente SQL. El respaldo diario de las 22:00 h se programa con el
  Programador de tareas de Windows:

```bat
schtasks /Create /TN "Dogtor respaldo diario" /SC DAILY /ST 22:00 ^
  /TR "C:\dogtor\.venv\Scripts\python.exe C:\dogtor\scripts\respaldo.py respaldar"
```

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
bash scripts/proteger_ramas.sh JECR2005/dogtor-veterinaria               # S0-06: solo pull requests revisados
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
| S0-06 | Ramas main/develop protegidas (`scripts/proteger_ramas.sh`) | Falta: ejecutar el script |
| S0-07 | Convenciones y plantillas de PR e issues | Hecho |
| S0-08 | `.gitignore` y `.env.example` | Hecho |
| S0-09 | VS Code y ruff comunes | Hecho |
| S0-10 | Dependencias | Falta: fijar versiones exactas con `pip freeze` tras la primera instalación |
| S0-11 | Configuración por entorno | Hecho |
| S0-12 | Ocho apps con models/services/views/urls | Hecho |
| S0-13 | Usuario propio (Tabla 3.38) | Hecho |
| S0-14 | 26 tablas en SQL Server (`bd/01_tablas.sql`) y sus modelos | Hecho · Ejecutado en SQL Server 2022 el 13/11/2026: 19/19 pruebas · Falta: migraciones de Django |
| S0-15 | Índices recomendados | Hecho (en `bd/01_tablas.sql`) |
| S0-16 | Plantilla base con menú por rol | Hecho |
| S0-17 | pytest y cobertura | Hecho |
| S0-18 | Integración continua con SQL Server (`.github/workflows/ci.yml`) | Falta: primera ejecución en GitHub |
| S0-19 | Datos ficticios (`cargar_datos_prueba`) | Hecho |
| S0-20 | Pruebas de humo por app | Hecho |
| S0-21 | Respaldo y restauración (`scripts/respaldo.py`) | Hecho · Falta: primera prueba con la base del proyecto |
| S0-22 | README | Hecho |

Al completar la lista: `git tag -a v0.0-S0 -m "Línea base del entorno"`.
