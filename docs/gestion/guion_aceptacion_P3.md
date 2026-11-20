# Guion de prueba de aceptación de P3 «Núcleo clínico y estética» (S3-17)

> Apartado 4.5.2.3 y Tabla 4.14. La ejecuta quien evalúa el prototipo, **sin ayuda del equipo de desarrollo**,
> en el entorno local con los datos ficticios. Quien acompaña solo observa y anota; no explica ni toca el teclado.
> Al terminar, los resultados pasan al registro de ejecución (`resultados_pruebas.md`, Tabla 4.19) y al acta de P3.
> La regresión automática de este guion está en `tests/sistema/test_TA_escenarios_P3.py`.

| Campo | Valor |
|---|---|
| Línea base evaluada | `develop` en el commit: ______ (en P3 cerrado será `v0.3-P3`) |
| Fecha | ____/____/2026 |
| Evaluador y roles que representa | ______________________ (Veterinario, Recepcionista y Estilista) |
| Observador | ______________________ |
| Hora de inicio / fin | ____:____ / ____:____ |

## Antes de empezar (lo prepara el observador, sin el evaluador presente)

1. SQL Server encendido (`Get-Service MSSQLSERVER` o `Get-Service 'MSSQL$SQLEXPRESS'` → `Running`).
2. Datos ficticios limpios **del mismo día de la prueba**: las fechas de las citas y las próximas dosis se calculan
   con el día en que se cargan.
   ```
   .venv\Scripts\activate
   python bd/ejecutar.py --recrear
   python manage.py cargar_datos_prueba
   python manage.py runserver
   ```
3. Abrir `http://127.0.0.1:8000`. Cuentas: `veterinario`, `recepcion` y `estilista` (contraseña de `.env`).
4. Anotar si **mañana es domingo**: ☐ Sí ☐ No. Si es domingo no hay cita de Canela mañana y en TA-05 los números
   bajan en uno.
5. Cerrar cualquier otra pestaña del sistema.

Datos ficticios que usa el guion:

| Cliente (canal) | Mascota | Lo que tiene hoy |
|---|---|---|
| Elena Torres (WhatsApp) | Max, Labrador, **alérgico a la penicilina** | Consulta general hoy a las 10:00 con Laura Medina (veterinaria) |
| Jorge Salas (Teléfono) | Michi, gata siamesa | Su vacuna antirrábica vence **en 3 días** |
| Pedro Ibarra (WhatsApp) | Rocky, Schnauzer | Su desparasitante vence en 4 días (todavía no se avisa) |
| Ana Lucía Vega (Correo) | Canela, Poodle | Baño hoy a las 12:00 con Mario Estrada (estilista); corte mañana a las 11:00 |

---

## TA-04 · Firmar una consulta con una vacuna y una receta

**Evalúa:** Veterinario · **Requisitos:** RF-06, RF-07, RF-08, RD-01, RD-07, RD-08, RD-09 · **Criterio de aceptación
(Tabla 3.1):** el lote baja una sola vez y la receta no descuenta existencias; solo firma quien tiene cédula.

Entrar como **veterinario**. Leer cada paso al evaluador **tal como está escrito** y anotar el resultado.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Abra sus consultas de hoy.» | Con **Consultas del día** (barra superior): Max a las 10:00 con la etiqueta roja **Alergias**. | | |
| 2 | «Atienda a Max: anote que viene a revisión anual y vacuna, y que pesa 29.1 kg.» | Al pulsar **Atender** se ve la alerta roja «Alergias: Penicilina». Al abrir: «Consulta de Max abierta.» | | |
| 3 | «Aplique una dosis de vacuna antirrábica, 1 mL subcutánea, con la siguiente dosis en un año.» | Al elegir la vacuna dice «se tomará del lote VAC-002-A». Al registrar: «Aplicación registrada: Vacuna antirrábica, lote VAC-002-A. El lote ya se descontó.» | | |
| 4 | «Recete amoxicilina: 1 tableta cada 12 horas por 7 días.» | Con **Emitir receta**: «Receta R-2026-00001 emitida.» y el botón **PDF** abre la receta en tamaño carta con el folio. | | |
| 5 | «Intente firmar la consulta.» | No deja firmar: «Antes de firmar capture: diagnóstico.» | | |
| 6 | «Anote temperatura 38.6, diagnóstico “Sano”, guarde y firme.» | Con **Sí, firmar**: «Consulta firmada. La cita quedó completada y el peso de Max se actualizó a 29.10 kg.» La consulta dice «Es de solo lectura (RD-07)» y ya no hay botones para aplicar ni recetar. | | |
| 7 | «Abra el historial clínico de Max.» | Arriba la consulta de hoy, **Firmada**, con la vacuna antirrábica (próxima en un año) y la receta R-2026-00001; abajo, la consulta anterior. | | |

**Lo comprueba el observador al terminar** (cuenta `administrador`, sin el evaluador):

| # | Revisión | Resultado esperado | Cumple (Sí/No) |
|---|---|---|---|
| 8 | Inventario → Vacuna antirrábica → Lotes y Movimientos | VAC-002-A pasó de **18 a 17**; hay **un solo** movimiento «Aplicación −1» con referencia «Consulta …». | |
| 9 | Inventario → Amoxicilina 250 mg | Sigue con **60** (20 en MED-001-A y 40 en MED-001-B): la receta no descontó. | |
| 10 | Abrir la consulta de Max como Administrador | La ve en solo lectura, **sin** botón «Firmar consulta» (solo firma el veterinario con cédula, RD-01). | |
| 11 | Administración → Empleados → Laura Medina: borrar la cédula y guardar | No se guarda: «La cédula profesional es obligatoria para el puesto Veterinario.» Salir **sin guardar**. | |

**Resultado TA-04:** ☐ Aprobado (todos los pasos «Sí») ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## TA-05 · Revisar la lista de recordatorios

**Evalúa:** Recepcionista · **Requisitos:** RF-09, RF-05 · **Criterio de aceptación (Tabla 3.1):** tres días antes
de la próxima dosis el cliente aparece con su canal preferido y, al marcarlo Contactado, sale de los pendientes.

Cerrar sesión y entrar como **recepcion**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Revise cuántos clientes tiene que contactar hoy.» | La tarjeta **Recordatorios pendientes** dice **2** (1 si mañana es domingo), y el menú Recordatorios tiene el mismo número. | | |
| 2 | «Abra la lista y diga a quién hay que avisar y por qué.» | **Jorge Salas · Michi · Próxima dosis: Vacuna antirrábica**, «en 3 días», canal **Teléfono** con el botón **Llamar**. **Ana Lucía Vega · Canela · Cita: Corte y estética a las 11:00**, «mañana», canal **Correo** con **Escribir correo**. Rocky **no** aparece. | | |
| 3 | «Revise el mensaje que se le enviaría a Ana Lucía.» | Al pulsar **Escribir correo** se abre el correo dirigido a ana.vega@example.com con el recordatorio de la cita ya escrito. Cerrar el correo sin enviarlo. | | |
| 4 | «Ya llamó a Jorge y confirmó. Regístrelo.» | Con **Contactado**: «Jorge Salas: contactado.» Michi sale de «Por contactar» y aparece en **Contactados hoy** con la hora y el nombre de Sofía. | | |
| 5 | «Revise otra vez el Inicio.» | **Recordatorios pendientes** baja a **1** (0 si mañana es domingo). | | |
| 6 | «Ana Lucía no contestó. Regístrelo.» (si apareció en el paso 2) | Con **Sin respuesta**: pasa a «Sin respuesta: volver a intentar» y el Inicio baja a **0**. | | |

**Resultado TA-05:** ☐ Aprobado ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## TA-06 · Registrar una atención de estética con un hallazgo y avisar

**Evalúa:** Estilista y Veterinario · **Requisitos:** RF-10, RD-04 · **Criterio de aceptación (Tabla 3.1):** el aviso
se muestra al veterinario y el registro aparece en el historial.

Cerrar sesión y entrar como **estilista** (si hay tableta, hacer esta prueba en ella).

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Revise qué atenciones tiene hoy.» | El Inicio dice **Atenciones por registrar: 1**. En **Estética**: la tarjeta de **Canela · Baño 12:00–13:00**, Programada, con el botón **Registrar atención**. | | |
| 2 | «Canela llegó con el pelaje opaco y nudos en las orejas, y le encontró costras en el lomo. Regístrelo y avise al veterinario.» | Si marca el aviso sin escribir hallazgos: «Para avisar al veterinario, describa el hallazgo.» Al guardar completo: «Atención de Canela registrada; la cita quedó completada. Se avisó al veterinario.» La tarjeta queda **Completada** con «Se avisó al veterinario». | | |

Cerrar sesión y entrar como **veterinario**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 3 | «Revise si tiene algún aviso.» | En el Inicio, **Avisos de estética: 1** (y un 1 junto a Estética en el menú); abajo, Canela con «Costras en el lomo» y el nombre de Mario Estrada. | | |
| 4 | «Revise el historial clínico de Canela.» | Aparece el registro de **Estética** de hoy con «Aviso al veterinario», el estado del pelaje y «Hallazgos: Costras en el lomo». | | |

**Resultado TA-06:** ☐ Aprobado ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## Calificación del personal (Tabla 3.20: promedio de al menos 4 de 5)

Al terminar, el evaluador califica **sin que el equipo opine** los cinco aspectos del apartado 4.5.2.3, una fila por
cada rol que representó:

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| (Veterinario) | | | | | | |
| (Recepcionista) | | | | | | |
| (Estilista) | | | | | | |

Observaciones del evaluador: ______________________________________________

## Al terminar (lo hace el líder)

1. Copiar a `docs/gestion/resultados_pruebas.md`, Tabla 4.19 (sección P3), las filas de TA-04, TA-05 y TA-06 con
   fecha, ejecutor, versión (commit), resultado y, si falló, el defecto.
2. Registrar cada defecto encontrado como DEF-nnn y cada sugerencia como OBS-nnn.
3. Pasar la calificación al acta de P3 (sección 4).
