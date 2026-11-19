# Revisión en tableta · P3 (OBS-04, S3-14)

Atiende la observación OBS-04 de LV-02 punto 6: «falta probar las pantallas en la tableta de la estética»
(evaluacion_P1.md y evaluacion_P2.md). Requisitos: RNF-02 (equipos de la clínica), RI-09 (objetivos de 44 px,
fuente de 16 px) y RI-10 (menú contraído a iconos).

## Cómo se revisa

Con la tableta de la estética o, si no está disponible, con Chrome o Edge: **F12 → icono de dispositivo
(Ctrl+Shift+M) → iPad Air**, en vertical (820 × 1180) y en horizontal (1180 × 820). Se entra con cada cuenta
y se recorre la pantalla haciendo la tarea, no solo mirándola.

Criterios por pantalla:

1. No aparece barra de desplazamiento horizontal de la página (las tablas se desplazan dentro de su caja).
2. Todos los botones, enlaces del menú y casillas se pueden tocar con el dedo sin acertar a otro.
3. El texto se lee sin hacer zoom.
4. Lo importante (botón principal, alertas de alergias y avisos) se ve sin buscarlo.

## Lo que ya cuida el código (pruebas automáticas)

| Regla | Dónde | Prueba |
|---|---|---|
| La página se adapta al ancho (viewport) | `templates/base.html` | `test_plantillas_tableta.py` |
| Toda tabla se desplaza dentro de su caja | todas las plantillas en pantalla | `test_plantillas_tableta.py` (una por plantilla) |
| Botones y campos de 44 px; casillas más grandes al tocar | `static/css/dogtor.css` | `test_plantillas_tableta.py` |
| Menú contraído a iconos por debajo de 992 px, con el contador sobre el icono | `dogtor.css` | `test_plantillas_tableta.py` |
| Barra superior solo con iconos por debajo de 1200 px (el texto queda para lectores de pantalla) | `base.html`, `dogtor.css` | Revisión visual |
| Menú del estilista en la tableta: Inicio, Agenda, Estética y Mi cuenta (apartado 4.4) | `seguridad/context_processors.py` | `test_S3_14_menu_y_ayuda.py` |
| Agenda de estética en tarjetas con botón grande | `templates/estetica/dia.html` | TI-11 |

## Resultado de la revisión visual

| Pantalla | Rol | Vertical | Horizontal | Observación |
|---|---|---|---|---|
| Inicio | Estilista | Pendiente | Pendiente | |
| UI-16 Agenda de estética | Estilista | Pendiente | Pendiente | |
| UI-16 Registrar atención | Estilista | Pendiente | Pendiente | |
| UI-11 Consultas del día y consulta | Veterinario | Pendiente | Pendiente | |
| UI-12 Aplicaciones | Veterinario | Pendiente | Pendiente | |
| UI-13 Receta | Veterinario | Pendiente | Pendiente | |
| UI-14 Historial clínico | Veterinario | Pendiente | Pendiente | |
| UI-15 Recordatorios del día | Recepcionista | Pendiente | Pendiente | |
| UI-07 Agenda (calendario) | Recepcionista | Pendiente | Pendiente | |

Revisó: JECR2005 · Fecha: pendiente · Equipo: pendiente
