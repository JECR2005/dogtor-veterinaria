# Guion de prueba de aceptación de P2 «Abastecimiento» (S2-15)

> Apartado 4.5.2.3 y Tabla 4.14. La ejecuta quien evalúa el prototipo, **sin ayuda del equipo de desarrollo**,
> en el entorno local con los datos ficticios. Quien acompaña solo observa y anota; no explica ni toca el teclado.
> Al terminar, los resultados pasan al registro de ejecución (`resultados_pruebas.md`, Tabla 4.19) y al acta de P2.
> La regresión automática de este guion está en `tests/sistema/test_TA_escenarios_P2.py`.

| Campo | Valor |
|---|---|
| Línea base evaluada | `develop` en el commit: ______ (en P2 cerrado será `v0.2-P2`) |
| Fecha | ____/____/2026 |
| Evaluador y rol que representa | ______________________ (Administrador) |
| Observador | ______________________ |
| Hora de inicio / fin | ____:____ / ____:____ |

## Antes de empezar (lo prepara el observador, sin el evaluador presente)

1. SQL Server encendido (`Get-Service MSSQLSERVER` o `Get-Service 'MSSQL$SQLEXPRESS'` → `Running`).
2. Datos ficticios limpios, para que los números del guion coincidan:
   ```
   .venv\Scripts\activate
   python bd/ejecutar.py --recrear
   python manage.py cargar_datos_prueba
   python manage.py runserver
   ```
3. Abrir `http://127.0.0.1:8000` y tener a la mano la cuenta `administrador` (contraseña de `.env`).
4. Anotar una fecha de caducidad del **próximo año** para los lotes nuevos: ____/____/______.
5. Cerrar cualquier otra pestaña del sistema.

---

## TA-03 · Recibir un pedido y revisar las alertas

**Evalúa:** Administrador · **Requisitos:** RF-11, RF-12, RD-03, RD-05 · **Criterio de aceptación (Tabla 3.1):** se
crean los lotes con caducidad, las existencias aumentan y aparecen las alertas de stock mínimo y de caducidad a 30 días.

Entrar como **administrador**. Leer cada paso al evaluador **tal como está escrito** y anotar el resultado.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Revise en el Inicio cuántas alertas de inventario hay y ábralas.» | La tarjeta **Alertas de inventario** dice **5** (2 con stock bajo · 2 lotes por caducar · 1 vencido). En **Alertas**: Croquetas gato (0) y Vacuna triple felina (3 de 5) con stock bajo; VAC-001-A y MED-001-A caducan en 15 y 25 días; VAC-001-V vencido. | | |
| 2 | «Abra el pedido pendiente de la Distribuidora Veterinaria del Golfo y revise qué se pidió.» | Pedido **PC-0001**, Pendiente: Vacuna triple felina 20 × $140.00 y Amoxicilina 60 × $9.00; total **$3,340.00**. | | |
| 3 | «Reciba el pedido, pero guarde sin escribir la caducidad de la vacuna.» | No se recibe: «Capture la caducidad.» y «no se creó ningún lote». El pedido sigue Pendiente. | | |
| 4 | «Capture lo que llegó: vacuna 20, lote VTF-2701; amoxicilina 60, lote AMX-2701; las dos caducan el [fecha anotada]. Guarde.» | «Pedido PC-0001 recibido: 2 lotes con su entrada…»; el pedido queda **Recibido** y muestra los lotes que entraron. | | |
| 5 | «Revise en Inventario las existencias de la vacuna triple felina y de la amoxicilina.» | Vacuna triple felina **23** sin «Stock bajo»; Amoxicilina **120**. En la ficha de la vacuna, el lote VTF-2701 está Vigente y en Movimientos aparece la entrada **+20** con referencia PC-0001. | | |
| 6 | «Vuelva a revisar las alertas.» | La vacuna triple felina ya no aparece en stock bajo; siguen Croquetas gato, los dos lotes por caducar y el vencido. El Inicio dice **4**. | | |
| 7 | «Retire el lote vencido de la vacuna múltiple canina.» | Con **Desechar** y **Revisar ajuste** ve «Pasa de 4 a 0»; al confirmar, el lote queda «Agotado · caducó» y la alerta de vencido desaparece. El Inicio dice **3**. | | |

**Resultado TA-03:** ☐ Aprobado (todos los pasos «Sí») ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## Calificación del personal (Tabla 3.20: promedio de al menos 4 de 5)

Al terminar, el evaluador califica **sin que el equipo opine** los cinco aspectos del apartado 4.5.2.3:

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| (Administrador) | | | | | | |

Observaciones del evaluador: ______________________________________________

## Al terminar (lo hace el líder)

1. Copiar a `docs/gestion/resultados_pruebas.md`, Tabla 4.19 (sección P2), la fila de TA-03 con fecha, ejecutor,
   versión (commit), resultado y, si falló, el defecto.
2. Registrar cada defecto encontrado como DEF-nnn y cada sugerencia como OBS-nnn.
3. Pasar la calificación al acta de P2 (sección 4).
