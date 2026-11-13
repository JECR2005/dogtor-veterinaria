# Cómo trabajar en el repositorio de Dogtor

Convenciones del equipo (S0-07). Responden a la gestión de la configuración y la revisión entre pares
del plan de calidad (apartado 3.2.4, Tablas 3.18 y 4.3).

## Ramas

| Rama | Para qué | Quién escribe |
|---|---|---|
| `main` | Línea base estable de cada prototipo. Solo recibe merges desde `develop` al cerrar un prototipo. | Líder, vía pull request |
| `develop` | Integración del trabajo del prototipo en curso. | Todos, vía pull request |
| `feature/<requisito>-<tema>` | Una función. Ejemplo: `feature/rf-05-citas`, `feature/rd-05-lote-por-caducidad`. | Quien la desarrolla |
| `fix/def-<nnn>-<tema>` | Corrección de un defecto registrado. Ejemplo: `fix/def-007-cambio-negativo`. | Quien lo corrige |

Nadie hace `push` directo a `main` ni a `develop`; las reglas de protección de GitHub lo impiden (`scripts/proteger_ramas.sh`).

## Commits

Empiezan con el requisito, la regla o el defecto que atienden:

```
RF-05: calcula la hora de fin con la duración del servicio
RD-02: rechaza citas fuera del horario laboral
DEF-007: el cambio ya no puede ser negativo
S0: configura pytest y cobertura
```

## Pull requests

1. Abre el PR contra `develop` y enlaza el issue (`Cierra #12`).
2. Llena la plantilla: requisitos, pruebas y evidencia.
3. La integración continua debe quedar en verde (pruebas, cobertura, migraciones y ruff).
4. **Otra persona** revisa y aprueba (meta: 100 % de revisión entre pares, Tabla 3.20). Quien escribió el código no aprueba su propio PR.
5. Se integra con *squash merge* para que cada requisito quede en un commit en `develop`.

## Dónde va cada cosa dentro de una app

| Archivo | Contenido |
|---|---|
| `models.py` | Tablas del diccionario de datos (apartado 3.5). Nombres de tabla y columna iguales al diccionario. |
| `services.py` | Reglas de negocio (RD-xx). Se prueban sin pasar por la interfaz. |
| `views.py` | Pantallas. Verifican el permiso del rol en cada solicitud (RNF-01, RI-11). |
| `urls.py` | Rutas de la app. |

Las pruebas viven en `tests/unidad`, `tests/integracion` y `tests/sistema`, y su nombre de función incluye el
identificador del caso del apartado 4.5: `test_TU_05_lote_que_caduca_primero`.

## Cambios a la base de datos

- Todo cambio de modelo va con su migración en el mismo PR (`python manage.py makemigrations`).
- No se editan migraciones ya integradas en `develop`; se crea una nueva.
- Si un cambio contradice el diccionario de datos, se actualiza también el apartado 3.5 y se registra en `docs/decisiones.md`.

## Dependencias

Agregar o actualizar una dependencia requiere, en el mismo PR: versión en `requirements*.txt`, renglón en
`docs/componentes.md` con su licencia, y todas las pruebas en verde (R10).

## Cierre de un prototipo

1. Se cumplen los criterios de salida de la Tabla 4.11 (ver `docs/gestion/acta_aceptacion_prototipo.md`).
2. Se integra `develop` en `main` y se crea la etiqueta: `git tag -a v0.1-P1 -m "Línea base P1"`.
3. Se llenan la Tabla 4.20, el formato LV-R y la matriz de riesgos (`docs/gestion/`).
