# Acta de aceptación del prototipo P1 (Anexo C del contrato)

| Campo | Valor |
|---|---|
| Proyecto | Dogtor: Veterinaria & Petcare |
| Prototipo | P1 · nombre: Núcleo de operación |
| Línea base evaluada (etiqueta git) | v0.1-P1 |
| Fecha de entrega para evaluación | 17/11/2026 |
| Fecha límite de respuesta (5 días hábiles, cláusula Sexta) | 24/11/2026 |
| Evaluadores (rol que representan) | Castillo Ruiz Jesus Enrique, en el papel de Recepcionista y de Administrador (Tabla 3.1) |
| Responsable de calidad del prototipo | Cisneros Guevara Carlos Daniel |

## 1. Criterio de validación del prototipo (Tabla 3.1)

| Criterio | Cumple (Sí/No) | Observación |
|---|---|---|
| La recepcionista agenda, reprograma y cancela una cita, incluido el alta de un cliente y su mascota, sin ayuda del equipo | Sí | TA-01: 8 de 8 pasos sin ayuda |
| El sistema rechaza un empalme y una cita fuera del horario laboral | Sí | TA-02: «Empalme de horario» y «Fuera de horario laboral», cada uno con qué hacer |

## 2. Requisitos incluidos y su criterio de aceptación

| Requisito | Caso(s) de prueba | Resultado | Observación |
|---|---|---|---|
| RF-01 Clientes | TI-01, TA-01 | Aprobado | No se guarda sin aviso de privacidad |
| RF-02 Mascotas | TI-01, TA-01 | Aprobado | La mascota queda ligada al cliente y con expediente (RD-10) |
| RF-03 Empleados, horario y usuarios | TU-05 | Aprobado | Veterinario sin cédula no se guarda (RD-01) |
| RF-04 Catálogo de servicios | TI-02 | Aprobado | La duración del servicio define la hora de fin |
| RF-05 Citas | TU-01 a TU-04, TI-02, TA-01, TA-02 | Aprobado | Agendar, reprogramar, cancelar y completar |
| RD-02 Horario y empalmes | TU-01 a TU-03, TA-02 | Aprobado | Incluye valores límite |
| RD-04 Puesto del servicio | TU-04, TI-02 | Aprobado | Solo aparecen empleados del puesto requerido |
| RD-10 Expediente por mascota | TI-01 | Aprobado | |
| RNF-01 Seguridad de acceso | TU-13, TS-01 (adelantado) | Aprobado | Bloqueo al 5.º intento; cada rol abre solo lo suyo |

## 3. Criterios de salida (Tabla 4.11)

| Criterio | Meta | Resultado |
|---|---|---|
| Defectos críticos abiertos | 0 | 0 |
| Defectos mayores abiertos | ≤ 3 | 0 |
| Reglas RD del prototipo con prueba que intenta violarlas | 100 % | 100 % (4 de 4) |
| Cobertura de pruebas unitarias | ≥ 60 % | 96 % |
| Promedio de cada lista LV aplicable | ≥ 80 % y ningún punto < 60 % | LV-01 91 %, LV-02 90 %, LV-03 94 %, LV-04 100 %; mínimo 80 % |
| Restauración de un respaldo (RNF-04) | < 120 min | 0.60 s |

Detalle en `evaluacion_P1.md`; registro de casos y defectos en `resultados_pruebas.md`.

## 4. Calificación del personal (meta ≥ 4 de 5)

| Evaluador (rol) | Facilidad de uso | Rapidez | Claridad de los mensajes | Confianza en los datos | Utilidad para el trabajo diario | Promedio |
|---|---|---|---|---|---|---|
| Recepcionista y Administrador (JECR2005) | 5 | 5 | 5 | 5 | 5 | 5.0 |

Registrado con base en la evaluación del 17/11/2026: «todas las pruebas con 5; el sistema es lo suficientemente
intuitivo y simple de usar». Si algún aspecto merece otra calificación, se corrige aquí antes de firmar.

## 5. Observaciones del personal

| ID | Observación | Atención |
|---|---|---|
| OBS-01 | Al generar una nueva cita, mostrar de entrada la lista de clientes con sus mascotas, sin tener que buscar. | Atendida el 17/11/2026 (PR #56). |

## 6. Decisión

- [x] **Aceptado**
- [ ] **Aceptado con observaciones** (se atienden en el prototipo siguiente; ver issues: ___ )
- [ ] **No aceptado** (motivo):

| Por EL CLIENTE | Por EL EQUIPO |
|---|---|
| Nombre, cargo y firma: ______________________ | Castillo Ruiz Jesus Enrique, líder del proyecto · firma: ______________________ |
| | Cisneros Guevara Carlos Daniel, responsable de calidad de P1 · firma: ______________________ |
