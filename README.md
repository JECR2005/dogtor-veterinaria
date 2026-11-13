# Dogtor · Sistema de gestión veterinaria

Sistema web de gestión de clientes, citas, expedientes clínicos, inventario y ventas para
**Dogtor: Veterinaria & Petcare** (Tampico, Tamaulipas). Proyecto de la asignatura Gestión de Proyectos de
Software, Equipo 1.

- **Ciclo de vida:** prototipado evolutivo con desarrollo basado en componentes (apartado 3.1), prototipos P1 a P5.
- **Plataforma:** Python 3.12, Django 5.2 LTS, PostgreSQL 16, Bootstrap 5 (apartado 4.1).
- **Estado:** Sprint 0 (preparación del entorno). Ver la lista de cierre al final.

## Instalación local (S0-22)

Objetivo: cualquier integrante levanta el sistema en menos de 30 minutos siguiendo estos pasos.

### 1. Requisitos

| Programa | Versión | Nota |
|---|---|---|
| Python | 3.12 o 3.13 | En Windows, marcar "Add python.exe to PATH" al instalar. |
| PostgreSQL | 16 | Incluye `psql`, `pg_dump` y `pg_restore`. En Windows, agregar `C:\Program Files\PostgreSQL\16\bin` al PATH. |
| Git | Vigente | |
| Visual Studio Code | Vigente | Al abrir la carpeta, aceptar las extensiones recomendadas (`.vscode/extensions.json`). |

### 2. Base de datos

Con `psql` como usuario `postgres`:

```sql
CREATE USER dogtor_app WITH PASSWORD 'cambiar-esta-contrasena' CREATEDB;
CREATE DATABASE dogtor OWNER dogtor_app;
```

`CREATEDB` permite que pytest cree su base de pruebas y que `scripts/respaldo.py probar` cree la base temporal.

### 3. Proyecto

```bash
git clone <url-del-repositorio> dogtor
cd dogtor
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # Windows: copy .env.example .env
```

Edita `.env`: pon la contraseña de `dogtor_app` en `DB_CONTRASENA`. El archivo `.env` nunca se sube al repositorio.

### 4. Migraciones, cuenta inicial y datos ficticios

```bash
python manage.py migrate
python manage.py createsuperuser        # crea también el empleado Administrador (docs/decisiones.md, D-05)
python manage.py cargar_datos_prueba    # 50 mascotas ficticias, catálogos y 4 cuentas de prueba
python manage.py runserver
```

Abre http://127.0.0.1:8000/ (inicio) y http://127.0.0.1:8000/salud/ (debe responder `{"estado": "ok"}`).
El sitio de administración del entorno local está en http://127.0.0.1:8000/admin-local/.

> **Solo la primera vez, solo el responsable de base de datos:** antes de `migrate` ejecuta
> `python manage.py makemigrations seguridad catalogos agenda clinico inventario ventas recordatorios`,
> revisa que se generen las 26 tablas y sube las migraciones en un pull request. Los demás integrantes ya
> solo ejecutan `migrate`.

### 5. Pruebas

```bash
pytest                    # todas
pytest -m unidad          # solo unidad (no usan la base de datos)
pytest --cov              # con cobertura (meta ≥ 60 %, Tabla 3.20)
ruff check .              # estilo y análisis estático
```

## Respaldo y restauración (RNF-04)

```bash
python scripts/respaldo.py respaldar                       # respaldo completo + copia externa + retención 30 días
python scripts/respaldo.py probar --prototipo P1           # restauración cronometrada; se anota en docs/gestion/
python scripts/respaldo.py restaurar ARCHIVO --base NOMBRE # restaurar en un servidor limpio
```

La prueba de restauración se ejecuta **una vez por prototipo** y su tiempo debe ser menor a 120 minutos.

## Estructura (Tabla 4.24)

```
dogtor/
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

Cada app separa `models.py` (tablas del diccionario), `services.py` (reglas de negocio) y `views.py` (pantallas).
Las reglas de trabajo del equipo están en [CONTRIBUTING.md](CONTRIBUTING.md).

## Puesta en marcha del repositorio en GitHub (una sola vez, el líder)

```bash
git remote add origin https://github.com/USUARIO/dogtor.git
git push -u origin main develop
bash scripts/proteger_ramas.sh USUARIO/dogtor               # S0-06: solo pull requests revisados
python scripts/crear_issues.py --repo USUARIO/dogtor --dry-run
python scripts/crear_issues.py --repo USUARIO/dogtor        # S0-02: 34 issues, milestones P1 a P5
```

## Lista de cierre del Sprint 0

| ID | Actividad | Estado |
|---|---|---|
| S0-01 | Roles y suplentes (`docs/gestion/roles.md`) | Falta: llenar titulares y firmar |
| S0-02 | Backlog de 34 requisitos (`docs/gestion/backlog.csv`, `scripts/crear_issues.py`) | Falta: ejecutar el script en GitHub |
| S0-03 | Plantillas de gestión (`docs/gestion/`) | Hecho |
| S0-04 | Registro de componentes y licencias (`docs/componentes.md`) | Hecho |
| S0-05 | Repositorio con carpetas de código, documentación y pruebas | Falta: crear el remoto en GitHub |
| S0-06 | Ramas main/develop protegidas (`scripts/proteger_ramas.sh`) | Falta: ejecutar el script |
| S0-07 | Convenciones y plantillas de PR e issues | Hecho |
| S0-08 | `.gitignore` y `.env.example` | Hecho |
| S0-09 | VS Code y ruff comunes | Hecho |
| S0-10 | Dependencias | Falta: fijar versiones exactas con `pip freeze` tras la primera instalación |
| S0-11 | Configuración por entorno | Hecho |
| S0-12 | Ocho apps con models/services/views/urls | Hecho |
| S0-13 | Usuario propio (Tabla 3.38) | Hecho |
| S0-14 | Modelos de las 26 tablas con restricciones | Hecho · Falta: generar y subir migraciones |
| S0-15 | Índices recomendados | Hecho |
| S0-16 | Plantilla base con menú por rol | Hecho |
| S0-17 | pytest y cobertura | Hecho |
| S0-18 | Integración continua (`.github/workflows/ci.yml`) | Falta: primera ejecución en GitHub |
| S0-19 | Datos ficticios (`cargar_datos_prueba`) | Hecho |
| S0-20 | Pruebas de humo por app | Hecho |
| S0-21 | Respaldo y restauración (`scripts/respaldo.py`) | Hecho · Falta: primera prueba con la base del proyecto |
| S0-22 | README | Hecho |

Al completar la lista: `git tag -a v0.0-S0 -m "Línea base del entorno"`.
