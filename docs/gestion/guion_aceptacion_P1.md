# Guion de pruebas de aceptación de P1 «Núcleo de operación» (S1-21)

> Apartado 4.5.2.3 y Tabla 4.14. Las ejecuta quien evalúa el prototipo, **sin ayuda del equipo de desarrollo**,
> en el entorno local con los datos ficticios. Quien acompaña solo observa y anota; no explica ni toca el teclado.
> Al terminar, los resultados pasan al registro de ejecución (`resultados_pruebas.md`, Tabla 4.19) y al acta de P1.

| Campo | Valor |
|---|---|
| Línea base evaluada | `develop` en el commit: ______ (en P1 cerrado será `v0.1-P1`) |
| Fecha | ____/____/2026 |
| Evaluador(es) y rol que representan | ______________________ (Recepcionista) · ______________________ (Administrador) |
| Observador | ______________________ |
| Hora de inicio / fin | ____:____ / ____:____ |

## Antes de empezar (lo prepara el observador, sin el evaluador presente)

1. SQL Server encendido: `Get-Service 'MSSQL$SQLEXPRESS'` → `Running`.
2. Sistema arrancado: `.\.venv\Scripts\python.exe manage.py runserver` → abrir `http://127.0.0.1:8000`.
3. Cuentas de prueba: `recepcion` y `administrador` (contraseñas en `.env` / acordadas con el líder).
4. Elegir un **día hábil próximo** (lunes a sábado) y un **veterinario con horario** ese día; anotarlos aquí:
   día ______________ · veterinario ______________ · su jornada ____:____ a ____:____.
5. Cerrar cualquier otra pestaña del sistema.

---

## TA-01 · Alta de cliente y mascota; agendar, reprogramar y cancelar una cita

**Evalúan:** Recepcionista y Administrador · **Requisitos:** RF-01, RF-02, RF-05 · **Criterio de aceptación:** las
operaciones se completan **sin ayuda** del equipo de desarrollo.

Entrar como **recepcion**. Leer cada paso al evaluador **tal como está escrito** y anotar el resultado.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Lo logró sin ayuda? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Registre a un cliente nuevo: Mariana Ruiz Prueba, teléfono 833 555 0101, prefiere WhatsApp.» Intentar guardar **sin** marcar el aviso de privacidad. | No se guarda; aparece «Sin la aceptación del aviso de privacidad no se puede registrar al cliente.» | | |
| 2 | «Marque el aviso de privacidad y guarde.» | Se abre la ficha del cliente con el mensaje «Cliente … registrado». | | |
| 3 | «Registre a su perra: Luna, Labrador, hembra, 3 años, 22 kg. Es alérgica a la penicilina.» | Se abre la ficha de Luna con su expediente abierto hoy y la alerta roja de alergias. | | |
| 4 | «Agende para Luna una Consulta general con [veterinario] el [día] a las 10:00.» | La cita aparece en la Agenda ese día de 10:00 a 10:30, en estado Programada. | | |
| 5 | «Al cliente ya no le acomoda: reprograme la cita a las 12:00 del mismo día.» | La cita queda a las 12:00; el espacio de las 10:00 aparece libre en el calendario. | | |
| 6 | «Busque a Mariana desde la barra superior escribiendo solo “0101”.» | Aparece Mariana en los resultados. | | |
| 7 | «El cliente llamó para cancelar: cancele la cita.» Primero sin escribir motivo, después con el motivo «El cliente salió de viaje». | Sin motivo no se cancela y lo pide; con motivo queda Cancelada y el espacio libre. | | |
| 8 | Cerrar sesión y entrar como **administrador**. «Revise en el calendario cómo quedó la cita de Luna (marque “Mostrar canceladas”).» | Ve la cita Cancelada de Luna; no puede agendar ni modificar citas (solo consulta). | | |

**Resultado TA-01:** ☐ Aprobado (todos los pasos «Sí») ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## TA-02 · Rechazo de una cita fuera de horario y de una que se empalma

**Evalúa:** Recepcionista · **Requisitos:** RF-05, RD-02 · **Criterio de aceptación:** el sistema rechaza **ambas
citas con su mensaje**.

Entrar como **recepcion**.

| # | Lo que se le pide al evaluador | Resultado esperado | ¿Correcto? (Sí/No) | Observaciones |
|---|---|---|---|---|
| 1 | «Agende para Luna una Consulta general con [veterinario] el [día] a las 10:00.» | Se agenda (Programada, 10:00 a 10:30). | | |
| 2 | «Agende para otra mascota (por ejemplo, Firulais) una Consulta general con el **mismo** veterinario, el mismo día, a las 10:15.» | **No se guarda**; aparece «**Empalme de horario**» y la indicación «Elija otra hora u otro empleado, o reprograme la cita existente.» | | |
| 3 | «Ahora agéndela a las 10:30.» | Sí se guarda: terminar justo cuando la otra empieza no es empalme. | | |
| 4 | «Agende una consulta con el mismo veterinario 15 minutos antes de que termine su jornada» (por ejemplo, 18:45 si sale a las 19:00). | **No se guarda**; aparece «**Fuera de horario laboral**» y qué hacer. | | |
| 5 | «Agende a Luna otra cita a las 10:00 con **otro** veterinario.» | **No se guarda**; aparece «La mascota ya tiene una cita a esa hora…» (D-16, DEF-001). | | |

**Resultado TA-02:** ☐ Aprobado ☐ Fallido (anotar el paso y abrir un DEF-nnn)

---

## Calificación del personal (Tabla 3.20: promedio de al menos 4 de 5)

Al terminar, cada evaluador califica **sin que el equipo opine**:

| Evaluador | Facilidad de uso (1–5) | Cumple lo que necesito (1–5) | Promedio | Comentario |
|---|---|---|---|---|
| | | | | |
| | | | | |

## Al terminar (lo hace el líder)

1. Copiar a `docs/gestion/resultados_pruebas.md`, Tabla 4.19, una fila por caso (TA-01 y TA-02) con fecha,
   ejecutor, versión (commit), resultado y, si falló, el defecto.
2. Registrar cada defecto encontrado como DEF-nnn (clase Crítico, Mayor o Menor) y abrir su issue en GitHub.
3. Pasar la calificación al acta de P1 (`acta_aceptacion_prototipo.md`, sección 4).
