# Sprint 3 · Prototipo P3 «Núcleo clínico y estética»

| Campo | Valor |
|---|---|
| Duración | 3 semanas: 19 de noviembre al 9 de diciembre de 2026 |
| Requisitos | RF-06 Consulta e historial, RF-07 Recetas, RF-08 Aplicaciones, RF-09 Recordatorios, RF-10 Estética; RD-01 Cédula, RD-07 Solo lectura, RD-08 Receta en consulta abierta, RD-09 Descuento único |
| Issues (hito P3) | #6 RF-06 · #7 RF-07 · #8 RF-08 · #9 RF-09 · #10 RF-10 · #15 RD-01 · #21 RD-07 · #22 RD-08 · #23 RD-09 |
| Pantallas (Tabla 4.6) | UI-11 Consulta · UI-12 Aplicaciones · UI-13 Receta · UI-14 Historial · UI-15 Recordatorios · UI-16 Estética |
| Evalúan (Tabla 3.1) | Veterinario, Estilista y Recepcionista (JECR2005 en cada papel) |
| Criterio de validación (Tabla 3.1) | El veterinario firma una consulta con una vacuna y una receta; el lote baja una sola vez, la receta no descuenta existencias y la recepcionista ve el recordatorio 3 días antes de la próxima dosis. |
| Casos de prueba base (Tabla 4.17) | 11: TU-14, TU-15, TU-16, TU-17, TI-04, TI-08, TI-10, TI-11, TA-04, TA-05, TA-06 |
| Responsable de calidad (`roles.md`) | Aguilar Castillo Hugo Enrique |
| Línea base al cerrar | `v0.3-P3` |

## Actividades

Estado: ⬜ pendiente · 🔄 en curso · ✅ hecha. **Se trabaja por bloques:** un pull request por bloque, que JECR2005
prueba en su equipo e integra antes de pasar al siguiente.

### A. Arranque

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-01 | Plan del sprint (este archivo) | APE | Plan en `docs/gestion/` |
| ✅ | S3-02 | Decisión D-18: PDF con xhtml2pdf en lugar de WeasyPrint | RF-07, RF-13, R10 | Elegida el 19/11; `requirements.txt`, `reportes/services.py` (`pdf_desde_html`, `pdf_desde_plantilla`), plantilla base tamaño carta y prueba |
| ✅ | S3-03 | Datos ficticios de P3 | RF-06 a RF-10 | `cargar_datos_prueba` crea a Max (alergia, consulta hoy 10:00), Michi (vacuna en 3 días), Rocky (desparasitante en 4 días) y Canela (baño hoy 12:00, corte mañana), con consultas firmadas y aplicaciones que descontaron su lote |

### B. Consulta clínica

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-04 | Consultas del día del veterinario; abrir la consulta desde la cita con alerta de alergias (UI-11) | RF-06 | Pantalla con pruebas · `/clinica/` y «Atender consulta» en la cita |
| ✅ | S3-05 | Captura y Firmar con confirmación: solo con cédula; después, solo lectura; la cita pasa a Completada y se actualiza el peso | RF-06, RD-01, RD-07 | TU-14 y TI-08 en verde · el modelo también rechaza escribir una consulta firmada |
| ✅ | S3-06 | Historial clínico: consultas, aplicaciones, recetas y estética (UI-14) | RF-06, RD-10 | Pantalla con pruebas · `/clinica/mascotas/<id>/historial/`, enlazado desde la ficha de la mascota |

### C. Aplicaciones y recetas

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-07 | Aplicación con lote sugerido por caducidad, dosis y próxima fecha obligatoria; descuento único (UI-12) | RF-08, RD-05, RD-09 | TU-16 y TI-04 en verde · panel de aplicaciones en la consulta; «Quitar» devuelve al lote; el recordatorio de TI-04 se comprueba en el bloque D |
| ✅ | S3-08 | Receta con folio solo dentro de una consulta abierta, sin descontar existencias (UI-13) | RF-07, RD-08 | TU-15 en verde · folio consecutivo R-AAAA-NNNNN |
| ✅ | S3-09 | PDF de la receta en tamaño carta | RF-07, D-18 | Se descarga el PDF con folio · `/clinica/recetas/<id>/pdf/`, con cédula y alergias |

### D. Recordatorios

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-10 | Lista del día: próximas dosis a 3 días y citas de mañana, con el canal preferido (UI-15) | RF-09 | TU-17 en verde · `/recordatorios/`; se genera al abrir la lista o el Inicio y con `python manage.py generar_recordatorios`; el sábado avisa también las citas del lunes; el recordatorio de TI-04 ya se comprueba |
| ✅ | S3-11 | Contactado y Sin respuesta; agendar la siguiente dosis; contador en el Inicio de Recepción | RF-09, RF-05 | TI-10 en verde · el botón del canal abre WhatsApp, el correo o la llamada con el mensaje listo; «Contactado y agendar» abre la nueva cita con la mascota, la fecha y Vacunación; el Administrador solo consulta |

### E. Estética

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-12 | Agenda del estilista y registro de atención que completa la cita (UI-16) | RF-10, RD-04 | Pantalla con pruebas · `/estetica/` en tarjetas para la tableta, con día anterior y siguiente; solo el estilista asignado registra, el día de la cita y una vez; Veterinario y Administrador consultan |
| ✅ | S3-13 | Aviso al veterinario de un hallazgo, en su Inicio y en el historial | RF-10 | TI-11 en verde · el aviso pide describir el hallazgo; sale del Inicio cuando la mascota pasa a consulta y se muestra junto a las alergias al atenderla |

### F. Interfaz y seguridad

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-14 | Permisos de la Tabla 4.9, TS-01 con las rutas nuevas, Ayuda de los cuatro roles y revisión en tableta (OBS-04) | RNF-01, RNF-02, RNF-07 | Ningún rol ve más de lo suyo · Tabla 4.9 celda por celda, menú con contadores, Ayuda de P3 y reglas de tableta en verde; revisión visual en tableta correcta, sin observaciones (`revision_tableta_P3.md`, OBS-04 atendida) |

### G. Pruebas

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-15 | TU-14 a TU-17 y pruebas que intentan violar RD-01, RD-07, RD-08 y RD-09 | RD-01, RD-07 a RD-09 | Integración continua en verde · `test_S3_15_reglas_en_la_base.py`: la base ahora protege la consulta firmada (D-19, cambio `2026-11-19_RD-07_RD-08_consulta_firmada.sql`) |
| ✅ | S3-16 | TI-04, TI-08, TI-10 y TI-11 | RF-06 a RF-10 | Integración continua en verde · los cuatro en verde desde los bloques C, B, D y E |
| ✅ | S3-17 | Guion de TA-04, TA-05 y TA-06 y su regresión automatizada | Tabla 4.14 | `guion_aceptacion_P3.md` · regresión en `tests/sistema/test_TA_escenarios_P3.py` |
| ✅ | S3-18 | Aceptación como Veterinario, Recepcionista y Estilista con la calificación de los cinco aspectos | Tabla 3.1 | Aprobado, ≥ 4/5 (JECR2005) · TA-04, TA-05 y TA-06 aprobados el 20/11/2026 sin ayuda; 4/5 en los tres roles, sin sugerencias |

### H. Cierre del prototipo

| Estado | ID | Actividad | Requisito | Terminado cuando |
|---|---|---|---|---|
| ✅ | S3-19 | Criterios de salida y listas LV (hojas de EXP y REC) | Tabla 4.11 | `evaluacion_P3.md` · LV-01 93 %, LV-02 95 %, LV-03 93 %, LV-04 100 %; calidad global 95 % |
| ✅ | S3-20 | Prueba de restauración con datos de P3 | RNF-04 | < 120 min (JECR2005, en SSMS) · 1.84 s, 10.09 MB, 33 de 33 tablas y la vista (`registro_restauraciones.md`) |
| ✅ | S3-21 | Acta de P3, Tabla 4.20, LV-R y riesgos R13, R08 y R09 | APE | Documentos en `docs/gestion/` · `acta_aceptacion_P3.md` (Aceptado, firmas pendientes); R13 bajó a Medio |
| ⬜ | S3-22 | `develop` → `main` y release `v0.3-P3` | — | Línea base publicada (JECR2005 integra) |

## Forma de trabajo en este sprint

- Una rama `feature/s3-<bloque>` y un pull request a `develop` por bloque; la integración continua debe quedar en
  verde antes de integrarlo, y se integra después de probarlo.
- Después de cada `git pull` que cambie `requirements.txt`, ejecutar `pip install -r requirements-dev.txt`.
- Los cambios al esquema siguen `bd/cambios/LEEME.md`.
