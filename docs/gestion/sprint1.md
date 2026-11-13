# Sprint 1 · Prototipo P1 «Núcleo de operación»

| Campo | Valor |
|---|---|
| Duración | 3 semanas: 16 de noviembre al 4 de diciembre de 2026 (S2 a S4 del plan) |
| Requisitos | RF-01 a RF-05, RD-02, RD-04, RD-10, RNF-01; RNF-03 y RNF-08 en su parte de P1 |
| Issues (hito P1) | #1 RF-01 · #2 RF-02 · #3 RF-03 · #4 RF-04 · #5 RF-05 · #16 RD-02 · #18 RD-04 · #24 RD-10 · #27 RNF-01 · #29 RNF-03 · #34 RNF-08 |
| Criterio de validación (Tabla 3.1) | La recepcionista agenda, reprograma y cancela una cita, incluido el alta de un cliente y su mascota, sin ayuda del equipo; el sistema rechaza un empalme y una cita fuera del horario laboral. |
| Casos de prueba base (Tabla 4.20) | 10: TU-01, TU-02, TU-03, TU-04, TU-05, TU-13, TI-01, TI-02, TA-01, TA-02 |
| Equipo en el repositorio | JECR2005 y Claude (decisión D-14); la evaluación de aceptación la hace JECR2005 como Recepcionista y Administrador |
| Línea base al cerrar | `v0.1-P1` |

> **Atención a la fecha de entrega académica (1 de diciembre).** La semana 3 cruza esa fecha. Si en la entrega se
> espera una demostración de P1, adelantar las pruebas de aceptación (S1-21) al 27 de noviembre y presentar el
> prototipo en su estado de ese día; el cierre formal (S1-22 a S1-25) puede quedar para el 4 de diciembre.

## Actividades

Estado: ⬜ pendiente · 🔄 en curso · ✅ hecha

### A. Arranque · semana 1

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| 🔄 | S1-01 | Activar la protección de `main` y `develop` (pendiente S0-06) y crear la etiqueta `v0.0-S0` | S0-06, D-14 | La regla aparece activa en GitHub |
| 🔄 | S1-02 | Entorno local en Windows con `scripts/instalar_local.ps1` | Tabla 4.3 | El sistema abre en http://127.0.0.1:8000 con datos ficticios |
| ✅ | S1-03 | Planeación del sprint: este plan, reporte semanal e issues asignados | APE | Plan y reporte en `docs/gestion/` |

### B. Seguridad y acceso · semana 1

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S1-04 | Inicio y cierre de sesión (UI-01); bloqueo al 5.º intento; reactivación por el Administrador | RNF-01 | Pasa TU-13 |
| ⬜ | S1-05 | Permiso del rol validado en cada vista (Tabla 4.9), aunque se escriba la dirección | RNF-01, RI-11 | Sin permiso → «Acceso denegado» |
| ⬜ | S1-06 | Mi cuenta: cambiar contraseña | RNF-01 | La nueva funciona y la anterior no |
| ⬜ | S1-07 | Servicio de bitácora para bajas de clientes y reactivaciones | RNF-03 | Cada baja deja registro con valores previos |

### C. Catálogos · semana 2

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S1-08 | Clientes (UI-05): búsqueda, alta con aviso obligatorio, edición, baja lógica, búsqueda global | RF-01, RNF-08 | Sin aviso no se guarda; el dado de baja no aparece en búsquedas |
| ⬜ | S1-09 | Mascotas (UI-06): alta con expediente en la misma transacción; ficha del cliente con sus mascotas | RF-02, RD-10 | Pasa TI-01 |
| ⬜ | S1-10 | Empleados y usuarios (UI-03): puesto, horario semanal, cédula para veterinario, cuenta con rol | RF-03, RD-01 | Pasa TU-05 |
| ⬜ | S1-11 | Catálogo de servicios (UI-04) | RF-04, RD-04 | La duración define la hora de fin |

### D. Agenda · semana 2

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S1-12 | Servicio de agenda: hora de fin, horario laboral, empalmes con bloqueo, puesto compatible (procedimiento 4.3) | RD-02, RD-04 | Pasan TU-01 a TU-04 |
| ⬜ | S1-13 | Agendar, reprogramar, cancelar con motivo y completar | RF-05 | El espacio se libera de inmediato |
| ⬜ | S1-14 | Agenda (UI-07) con FullCalendar, filtro por empleado y botón «Nueva cita» | RF-05, D-07 | Pasa TI-02 |

### E. Interfaz común · semanas 1 y 2

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ⬜ | S1-15 | Bootstrap, iconos y FullCalendar dentro del proyecto (sin depender de internet) | R07, R10 | La interfaz carga sin internet |
| ⬜ | S1-16 | Panel de inicio (UI-02) por rol con las citas del día | UI-02 | Cada rol ve su panel |
| ⬜ | S1-17 | Mensajes con las frases de las reglas y formato local | RI-08, RI-13 | Coinciden con el documento |

### F. Pruebas · semana 3

| Estado | ID | Actividad | Casos |
|---|---|---|---|
| ⬜ | S1-18 | Pruebas de unidad | TU-01, TU-02, TU-03, TU-04, TU-05, TU-13 |
| ⬜ | S1-19 | Pruebas de integración | TI-01, TI-02 |
| ⬜ | S1-20 | Acceso por dirección directa a cada pantalla de P1 con cada rol | Adelanto de TS-01 |
| ⬜ | S1-21 | Pruebas de aceptación con el guion | TA-01, TA-02 |

### G. Cierre del prototipo · semana 3

| Estado | ID | Actividad | Terminado cuando |
|---|---|---|---|
| ⬜ | S1-22 | Criterios de salida (Tabla 4.11) | 0 críticos, ≤ 3 mayores, cobertura ≥ 60 %, LV ≥ 80 % en SEG, CAT y AGE, satisfacción ≥ 4/5 |
| ⬜ | S1-23 | Prueba de restauración con datos de P1 (`bd/04_prueba_respaldo.sql`) | < 120 min |
| ⬜ | S1-24 | Acta de P1, Tabla 4.20, LV-R y riesgos R01, R02, R09 | Documentos en `docs/gestion/` |
| ⬜ | S1-25 | `develop` → `main` y etiqueta `v0.1-P1` | Línea base publicada |

## Forma de trabajo en este sprint

- Cada actividad de B a E se entrega en una rama `feature/<requisito>-<tema>` y un pull request a `develop`
  que enlaza su issue; la integración continua debe quedar en verde antes de integrarlo.
- JECR2005 revisa cada pull request (revisión entre pares, Tabla 3.20) y lo prueba en su entorno local.
- Avance semanal en `docs/gestion/semanas/`; la desviación no debe pasar de 10 %.
