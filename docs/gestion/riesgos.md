# Seguimiento de riesgos por prototipo (apartado 3.2.3)

Exposición = P × I. Niveles: 1–4 Bajo · 5–9 Medio · 10–14 Alto · 15–25 Crítico.
Al cerrar cada prototipo se reevalúan P e I; un riesgo que pase a crítico se escala de inmediato.

| ID | Riesgo | Base P×I | Nivel base | P1 | P2 | P3 | P4 | P5 | Responsable |
|---|---|---|---|---|---|---|---|---|---|
| R01 | Requisitos incompletos o cambiantes | 4×4=16 | Crítico | 3×4=12 · Alto. Requisitos de P1 estables; la única observación (OBS-01) se atendió el mismo día sin cambiar el alcance | 3×4=12 · Alto. Sin cambios de alcance; D-04 se resolvió como decisión técnica | | | | Líder |
| R02 | Subestimación de tiempos | 4×4=16 | Crítico | 3×4=12 · Alto. P1 terminó antes de su fecha (cierre previsto el 4/12); se mantiene vigilancia para P3, el más grande | 2×4=8 · Medio. P2 se construyó en 2 días de las 2 semanas previstas | | | | Líder |
| R03 | Indisponibilidad de un integrante | 3×3=9 | Medio | 3×3=9 · Medio. Sin cambio; suplencias definidas en `roles.md` | 3×3=9 · Medio. Sin cambio | | | | Líder |
| R04 | Baja adopción del sistema | 3×4=12 | Alto | 2×4=8 · Medio. Aceptación 5/5 y OBS-01 atendida | 2×4=8 · Medio. TA-03 aprobada sin ayuda, 4/5 | | | | Pruebas y capacitación |
| R05 | Pérdida de información | 3×5=15 | Crítico | 2×5=10 · Alto. Restauración probada en 0.60 s en un servidor limpio (S1-23) | 2×5=10 · Alto. Restauración con datos de P2 en 0.56 s; `--recrear` ahora es todo o nada (DEF-006) | | | | Base de datos |
| R06 | Acceso no autorizado o filtración | 3×5=15 | Crítico | 2×5=10 · Alto. TS-01 aprobado, bloqueo al 5.º intento (TU-13), DEF-002 y DEF-003 cerrados | 2×5=10 · Alto. TS-01 incluye Inventario y Compras: solo el Administrador | | | | Seguridad |
| R07 | Fallas de energía o internet | 4×3=12 | Alto | 4×2=8 · Medio. El cambio de laptop mostró que el sistema se reinstala y restaura con los scripts | 4×2=8 · Medio. Sin cambio | | | | Administrador de Dogtor |
| R08 | Inconsistencias de inventario | 4×3=12 | Alto | 4×3=12 · Alto. Sin cambio; se atiende en P2 (inventario) | 2×3=6 · Medio. Descuento por caducidad con bloqueo (adelanto de TS-12), CHECK en la base, kardex que cuadra, ajustes con motivo y confirmación | | | | Calidad |
| R09 | Errores en la agenda | 3×3=9 | Medio | 2×3=6 · Medio. RD-02 y D-16 con pruebas que intentan violarlas; bloqueo de filas al agendar; TA-02 aprobado | 2×3=6 · Medio. Sin cambio | | | | Desarrollo |
| R10 | Componentes de terceros | 3×3=9 | Medio | 2×3=6 · Medio. Dependencias fijadas en `requirements.txt`; FullCalendar servido localmente | 2×3=6 · Medio. Sin dependencias nuevas | | | | Seguridad |
| R11 | Incumplimiento normativo | 2×5=10 | Alto | 2×5=10 · Alto. Sin cambio; el aviso de privacidad ya se exige al registrar clientes | 2×5=10 · Alto. Sin cambio | | | | Líder y administrador |
| R12 | Deuda técnica | 3×3=9 | Medio | 2×3=6 · Medio. Cobertura 96 %, `ruff` en la CI y revisión en cada PR | 2×3=6 · Medio. Cobertura 96 %; dos defectos de herramientas de base corregidos con prueba | | | | Calidad |
| R13 | Error en dosis o recetas | 2×5=10 | Alto | 2×5=10 · Alto. Sin cambio; se atiende en P3 | 2×5=10 · Alto. Se atiende en P3; las existencias ya admiten dosis con decimales (D-04) | | | | Veterinario y desarrollo |
| R14 | Rendimiento insuficiente | 2×3=6 | Medio | 2×3=6 · Medio. Sin cambio; TS-05 y TS-06 en P5 | 2×3=6 · Medio. Sin cambio; TS-05 y TS-06 en P5 | | | | Base de datos |
| R15 | Falla del hospedaje | 2×3=6 | Medio | 2×3=6 · Medio. Sin cambio | 2×3=6 · Medio. Sin cambio | | | | Administrador de Dogtor |

Formato de cada celda: `P×I=valor` y una nota breve si cambió.

**Revisión de P1 (17/11/2026):** ningún riesgo quedó en nivel crítico; R01, R02, R05 y R06 bajaron de Crítico a Alto,
R04 y R07 de Alto a Medio, y R09, R10 y R12 bajaron su exposición dentro de Medio (de 9 a 6). La revisión la propone el responsable de calidad de P1 y la confirma el líder del proyecto.

**Revisión de P2 (18/11/2026):** ningún riesgo crítico. R08 (inventario) bajó de Alto a Medio con las reglas de P2 y
R02 de Alto a Medio; los demás se mantienen. La propone el responsable de calidad de P2 y la confirma el líder.
