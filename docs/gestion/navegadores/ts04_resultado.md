# TS-04 · Navegadores, tableta e impresión (RNF-02)

Generado por `python tests/carga/ts04_navegadores.py` (S5-15, D-27) contra el entorno con https
(D-25). Criterio de la Tabla 4.15: los flujos funcionan en los tres equipos y la impresión sale en
tamaño carta.

Fecha: 2026-11-21 18:52. ✅ funciona · ❌ falla (con el motivo) · — no instalado.

| Flujo | Chrome | Edge | Tableta 10" (Galaxy Tab S4) |
|---|---|---|---|
| Inicio de sesión (recepcion) | ✅ con certificado válido | ✅ con certificado válido | ✅ con certificado válido |
| Buscar cliente | ✅ 25 clientes en la página | ✅ 25 clientes en la página | ✅ 25 clientes en la página |
| Agendar cita | ✅ 12/12/2026 09:30 | ✅ 14/12/2026 09:00 | ✅ 14/12/2026 09:30 |
| Calendario | ✅ FullCalendar se dibujó | ✅ FullCalendar se dibujó | ✅ FullCalendar se dibujó |
| Agenda impresa (PDF) | ✅ carta horizontal | ✅ carta horizontal | ✅ carta horizontal |
| Generar y cobrar ticket | ✅ T-2026-01973 | ✅ T-2026-01974 | ✅ T-2026-01975 |
| Ticket en PDF | ✅ carta vertical | ✅ carta vertical | ✅ carta vertical |
| Inicio de sesión (veterinario) | ✅ con certificado válido | ✅ con certificado válido | ✅ con certificado válido |
| Consultas del día | ✅ lista del día | ✅ lista del día | ✅ lista del día |
| Guardar consulta | ✅ guardada | ✅ guardada | ✅ guardada |
| Receta en PDF | ✅ receta en carta vertical | ✅ receta en carta vertical | ✅ receta en carta vertical |
| Historial | ✅ línea de tiempo | ✅ línea de tiempo | ✅ línea de tiempo |
| Inicio de sesión (estilista) | ✅ con certificado válido | ✅ con certificado válido | ✅ con certificado válido |
| Agenda de estética | ✅ agenda de estética | ✅ agenda de estética | ✅ agenda de estética |

**Pantallas con desplazamiento horizontal:** Chrome: ninguno; Edge: ninguno; Tableta 10" (Galaxy Tab S4): ninguno.
