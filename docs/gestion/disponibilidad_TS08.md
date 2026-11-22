# TS-08 · Disponibilidad en el horario de atención (RNF-06)

Generado por `python scripts/monitor.py reporte` (S5-10). Medición en **periodo reducido**
(D-22): el monitor revisa `/salud/` cada 5 min de lunes a sábado de 9:00 a 19:00 mientras
el equipo está encendido; las horas sin revisión no cuentan como caída ni como disponibilidad
(se reporta la cobertura).
El mes completo de la Tabla 4.15 sigue en operación después de `v1.0`.

| Dato | Valor |
|---|---|
| Periodo | 21/11/2026 a 21/11/2026 |
| Horas laborales del periodo | 10 |
| Horas monitoreadas | 1.9 (19 % de cobertura) |
| Revisiones | 23 · 0 con caída |
| Caída sobre lo monitoreado | 0.00 % (meta < 1 %) |
| Respuesta típica (mediana) | 46 ms |
| Resultado | **Cumple** |

## Por día

| Día | Revisiones | Con caída | Caída |
|---|---:|---:|---:|
| sáb 21/11/2026 | 23 | 0 | 0.0 % |

## Caídas

Sin caídas en el periodo.
