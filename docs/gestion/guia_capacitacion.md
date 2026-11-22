# Guía de capacitación de Dogtor (S5-18)

> RNF-07 y Tabla 4.14 (TA-10): una persona que nunca ha usado el sistema, después de **30 minutos** de
> capacitación con esta guía, debe registrar un cliente y cobrar un ticket **sin ayuda en 10 minutos o menos**.
> La imparte el líder (o quien conozca el sistema) frente a la laptop de la clínica. La misma guía sirve para
> presentar el sistema al personal antes de la jornada simulada de TA-09.

## Reglas para quien capacita

- La persona capacitada **maneja el teclado y el ratón** desde el minuto 1; quien capacita solo señala y explica.
- Se practica con los **datos de práctica** de esta guía, no con los de la prueba TA-10 (otra clienta, otros
  productos): así la prueba mide lo que aprendió y no lo que memorizó.
- Al terminar los 30 minutos no se responden más preguntas. La ayuda que queda es la del propio sistema
  (**Ayuda** en el menú de la cuenta), igual que el primer día real de trabajo.

## Preparación (5 minutos antes, sin la persona presente)

1. Datos ficticios cargados y el sistema abierto en **https://dogtor.local** con Chrome o Edge (ver
   `guion_aceptacion_P5.md`, «Antes de empezar»).
2. Una cuenta de **Recepción** para la persona (`recepcion`) y la contraseña anotada en un papel que se le
   entrega en el minuto 1.
3. Un cronómetro.

**Orden con las pruebas:** la práctica crea clientes, citas y tickets. Para que los totales de TA-09 salgan
como dice su guion, el personal practica **antes** de recrear la base, y la persona nueva de TA-10 se capacita
**después** de terminar TA-09 (TA-10 no depende de los totales).

## Plan de la sesión (30 minutos)

| Minuto | Tema | Lo que hace la persona capacitada | Lo que debe quedarle claro |
|---|---|---|---|
| 0 – 3 | Entrar y ubicarse | Entra con su usuario y contraseña. Recorre el menú: Inicio, Clientes y mascotas, Agenda, Recordatorios, Ventas y caja. Abre **Ayuda**. | Cada quien usa solo su cuenta; con cinco intentos fallidos se bloquea. Verde = hecho; rojo = el mensaje dice qué corregir. |
| 3 – 6 | El Inicio | Lee las tarjetas del panel: citas del día, recordatorios, **Tickets con saldo**. | El Inicio dice qué falta por hacer hoy. |
| 6 – 13 | Buscar y registrar un cliente | Busca «8339990002» en la barra superior y abre a Jorge Salas. Luego registra a **Práctica Uno Ficticia**, tel. 833 555 0199, prefiere llamada; intenta guardar **sin** marcar el aviso de privacidad, lee el mensaje rojo, marca la casilla y guarda. Agrega su mascota **Bolita** (Gato, Siamés, hembra). | Siempre buscar antes de registrar para no duplicar. Sin aviso de privacidad no se guarda. La mascota abre su expediente sola. |
| 13 – 16 | Agendar una cita | Desde la ficha de Bolita: **Nueva cita**, Consulta general, con Laura Medina, el siguiente día hábil a las 17:00. Antes intenta el domingo y lee el mensaje. | La lista de empleados solo muestra a quien puede dar el servicio. Fuera de horario o con empalme no se guarda. |
| 16 – 26 | Cobrar | En **Ventas y caja**: **Nuevo ticket** → elige a Práctica Uno → agrega 1 **Collar ajustable mediano** y mira cómo se calcula el importe → **Generar ticket**. Registra un pago de $100 con tarjeta (queda saldo) y el resto en efectivo con un billete de $100 (lee el cambio). Abre **PDF para imprimir**. Luego intenta vender **Amoxicilina** sin folio y lee el mensaje. | El ticket descuenta el inventario al generarse. Se puede pagar en partes; el ticket queda **Pagada** con saldo cero. En efectivo el sistema calcula el cambio. Un medicamento con receta pide el folio R-… |
| 26 – 28 | Corte de caja | Abre **Corte de caja** y encuentra los dos pagos que hizo. | El corte se revisa al cerrar y debe coincidir con el efectivo en caja. |
| 28 – 30 | Dudas | Pregunta lo que quiera. Quien capacita responde mostrando dónde está en **Ayuda**. | Dónde buscar cuando no recuerde algo. |

Si la persona termina antes un tema, se adelanta al siguiente; si se atora, quien capacita **no toma el ratón**:
le indica qué botón buscar.

## Para el resto del personal (antes de TA-09)

Cada rol repasa con **Ayuda** su sección y hace una práctica corta con su cuenta (10 minutos por rol, no cuentan
para TA-10):

| Rol (cuenta) | Práctica | Sección de Ayuda |
|---|---|---|
| Veterinario (`veterinario`) | Abrir una consulta, aplicar una vacuna, emitir una receta, capturar el diagnóstico y firmar. Revisar el historial de la mascota. | Atender una consulta · Aplicar una vacuna · Emitir una receta · Firmar la consulta |
| Estilista (`estilista`) | Abrir su agenda de estética y ver cómo se registra una atención con hallazgo y aviso al veterinario (sin guardar). | Registrar la atención de estética |
| Administrador (`administrador`) | Revisar Inventario → Alertas, la ficha de un producto con sus movimientos y la **Bitácora** con filtros. | Productos y existencias · Revisar la bitácora |
| Todos | Imprimir la agenda del día y leer qué hacer si se va la luz o la red. | Si se va la luz o la red |

## Después de la sesión

- Anotar en el guion de TA-10 la hora de fin de la capacitación y quién la impartió.
- Si la persona pidió algo que **Ayuda** no explica, anotarlo como OBS-nnn para mejorar la ayuda.
