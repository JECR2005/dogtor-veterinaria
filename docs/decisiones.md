# Registro de decisiones técnicas

Decisiones tomadas al implementar el diseño (apartados 3.4, 3.5 y 4.1). Cada una indica qué se decidió,
por qué y si requiere actualizar el documento del proyecto. Las que dicen **"Actualizar documento: Sí"** deben
reflejarse en el apartado indicado antes de la entrega.

## D-01 · Llave sustituta en las tablas de detalle

- **Contexto:** el diccionario define llaves primarias compuestas en `detalle_receta` (id_receta + id_producto),
  `detalle_pedido` (id_pedido + id_producto) y `detalle_venta` (id_venta + numero_linea).
- **Decisión:** cada tabla de detalle tiene una llave sustituta (`id_detalle_receta`, `id_detalle_pedido`,
  `id_detalle_venta`) y una **restricción de unicidad** sobre la combinación del diccionario.
- **Motivo:** el soporte de llaves compuestas del ORM de Django es reciente y limitado (formularios, administración
  y relaciones). La unicidad garantiza la misma regla de negocio: no se repite un producto en una receta o pedido,
  ni un número de línea en un ticket.
- **Actualizar documento:** Sí. Apartado 3.5, Tablas 3.45, 3.53 y 3.55 (agregar la llave sustituta y marcar la
  combinación como UK).

## D-02 · Campos de texto opcionales como NULL

- **Decisión:** los campos de texto con "Nulo: Sí" en el diccionario se crean como `NULL` (no como cadena vacía).
- **Motivo:** fidelidad al diccionario y porque los campos únicos opcionales (cédula profesional, RFC del proveedor)
  necesitan `NULL` para admitir varios registros sin valor (ver D-12).
- **Actualizar documento:** No.

## D-03 · Restricciones CHECK adicionales

- **Decisión:** además de las listas de valores permitidos, la base valida reglas que el diccionario describe
  en texto: cédula obligatoria para Veterinario (RD-01), compatibilidad servicio–puesto (RD-04), motivo obligatorio
  al cancelar citas y ventas, fecha de firma en consultas firmadas, próxima fecha obligatoria en vacunas y
  desparasitantes y posterior a la aplicación (R13), signo de la cantidad según el tipo de movimiento, motivo en
  ajustes, saldo entre 0 y el total, ticket «Pagada» solo con saldo cero, cambio = recibido − monto, recordatorio
  con exactamente un origen coherente con su tipo, y aceptación obligatoria del aviso de privacidad (RNF-08).
- **Motivo:** la base protege las reglas aunque falle el código (apartado 4.6.1, "Restricciones en la base").
  Están en `bd/01_tablas.sql`, junto con el disparador que hace inmodificables los movimientos de inventario (RD-07).
- **Actualizar documento:** Opcional. Puede listarse en el apartado 4.6.1, Base de datos.

## D-04 · Cantidad decimal en aplicación contra existencias enteras (resuelta en S2-02)

- **Contexto:** `aplicacion.cantidad` y `detalle_venta.cantidad` son DECIMAL(8,2), pero
  `lote.cantidad_disponible` y `movimiento_inventario.cantidad` eran INT. Aplicar 0.5 mL de un frasco no podía
  descontarse de un lote entero.
- **Opciones:** (a) contar las existencias en la unidad mínima (mL, tabletas) como enteros, o (b) cambiar las
  existencias y los movimientos a DECIMAL.
- **Decisión (17/11/2026, líder del proyecto):** opción **(b)**. `lote.cantidad_disponible` y
  `movimiento_inventario.cantidad` pasan a **DECIMAL(10,2)**. Con (a), 0.5 mL seguiría sin poder descontarse y
  habría que convertir unidades al vender y al aplicar.
- **Alcance:** las compras siguen en unidades enteras (`detalle_pedido.cantidad_solicitada` y
  `cantidad_recibida` no cambian). Las restricciones se conservan: existencia nunca negativa (RD-05), signo según
  el tipo de movimiento y motivo en los ajustes.
- **Dónde:** `bd/01_tablas.sql`, `bd/cambios/2026-11-17_RD-05_cantidad_decimal.sql` (bases existentes),
  `inventario/models.py` y la migración `inventario/0002_cantidad_decimal.py`.
- **Actualizar documento:** Sí. Apartado 3.5: en la Tabla 3.49, `cantidad_disponible` tipo **DECIMAL(10,2)**;
  en la Tabla 3.50, `cantidad` tipo **DECIMAL(10,2)**.

## D-05 · Cuenta inicial del Administrador

- **Contexto:** toda cuenta pertenece a un empleado (`usuario.id_empleado` es obligatorio).
- **Decisión:** `python manage.py createsuperuser` crea también el empleado con puesto Administrador.
- **Actualizar documento:** No (el paso de instalación del apartado 4.6.1 sigue siendo válido).

## D-06 · Versión de Django

- **Decisión:** serie 5.2 LTS (soporte de seguridad hasta abril de 2028), desde la 5.2.4, que es la que pide
  mssql-django para el soporte completo de 5.2.
- **Actualizar documento:** Opcional. Apartado 4.1, Tabla 4.2.

## D-07 · Calendario con vistas estándar de FullCalendar

- **Decisión:** la vista por empleado de RF-05 se arma con las vistas estándar (licencia MIT) y un filtro por
  empleado, porque las vistas por recurso son de licencia comercial (ver `docs/componentes.md`).
- **Actualizar documento:** No.

## D-08 · Archivo de configuración de pruebas automatizadas

- **Decisión:** además de los entornos de la Tabla 4.3 (local, pruebas y producción) existe
  `config/settings/test.py` para pytest y la integración continua.
- **Actualizar documento:** No.

## D-09 · SQL Server en lugar de PostgreSQL

- **Contexto:** el apartado 4.1 eligió PostgreSQL; el equipo decidió usar Microsoft SQL Server.
- **Decisión:** SQL Server 2022 (Express para el local, Developer para desarrollo), con el conector oficial
  `mssql-django` y el ODBC Driver 18. Django 5.2 se mantiene.
- **Impacto:** el respaldo usa `BACKUP DATABASE` / `RESTORE` en lugar de `pg_dump` / `pg_restore`; la integración
  continua levanta un contenedor de SQL Server; Express no tiene Agente SQL, así que el respaldo diario se programa
  con el Programador de tareas de Windows; Express limita cada base a 10 GB (suficiente para una clínica).
- **Actualizar documento:** **Sí.** Apartado 4.1 (Tabla 4.2: base de datos, respaldo y monitoreo; criterio de
  costo), apartado 4.6.1 (requisitos del entorno, base de datos, instalación y despliegue, comandos de respaldo
  y restauración) y Tabla 4.28 (tarea de respaldo).

## D-10 · El esquema se programa en T-SQL (base de datos primero)

- **Decisión:** las 26 tablas, sus restricciones, índices, la vista de stock y el disparador de RD-07 se escriben
  a mano en `bd/01_tablas.sql` y `bd/02_vistas.sql`. Los modelos de Django usan esas tablas con
  `managed = False`: las migraciones de Django ya no crean ni modifican las tablas del sistema.
- **Motivo:** las tablas quedan programadas y revisables directamente en SQL Server (SSMS), con nombres de
  restricción propios (PK_, FK_, UQ_, CK_, DF_, IX_) y una sola fuente de verdad. Las pruebas automatizadas
  ejecutan los mismos scripts sobre la base de pruebas.
- **Consecuencia:** cada cambio de esquema lleva un script en `bd/cambios/` (ver `bd/cambios/LEEME.md`).
- **Actualizar documento:** Sí. Apartado 4.6.1, Base de datos ("se implementa con los scripts de bd/ en lugar
  de las migraciones de Django").

## D-11 · Tipos de datos en SQL Server

- **Decisión:** VARCHAR(n) → NVARCHAR(n); CHAR(n) → NCHAR(n); TEXT → NVARCHAR(MAX); DATETIME → DATETIME2;
  BOOLEAN → BIT. INT, SMALLINT, DECIMAL(p,s), DATE y TIME se conservan. Longitudes y nulos, iguales al diccionario.
- **Motivo:** NVARCHAR guarda acentos y la ñ sin depender de la intercalación y es el tipo que usa el conector
  de Django (evita conversiones implícitas que impiden usar índices). TEXT está obsoleto en SQL Server. DATETIME2
  tiene más precisión y rango. Las fechas y horas se guardan en UTC y Django las muestra en hora de Tampico.
- **Actualizar documento:** Sí. Apartado 3.5, convención de "Tipos" (agregar la equivalencia para SQL Server).

## D-12 · Unicidad de campos opcionales con índice filtrado

- **Contexto:** en SQL Server una restricción UNIQUE admite un solo NULL. La cédula profesional (solo la tienen los
  veterinarios) y el RFC del proveedor son UK opcionales.
- **Decisión:** `CREATE UNIQUE INDEX ... WHERE campo IS NOT NULL` (UX_empleado_cedula, UX_proveedor_rfc).
- **Actualizar documento:** No.

## D-13 · Disparador de inmutabilidad de movimientos (RD-07)

- **Decisión:** `TR_movimiento_inventario_inmutable` rechaza todo UPDATE y DELETE sobre `movimiento_inventario`.
  Usa `RAISERROR` con `XACT_ABORT OFF` (no `THROW`) para rechazar solo esa instrucción sin anular la transacción
  completa de la aplicación.
- **Verificado** el 13/11/2026 en SQL Server 2022 Express (16.0.1210) con `bd/03_prueba_esquema.sql`:
  el UPDATE y el DELETE se rechazan con el error 50000 y la transacción sigue utilizable (XACT_STATE = 1).
- **Actualizar documento:** Opcional. Tabla 4.27, RD-07, columna "En la base de datos".

## D-14 · Equipo de dos personas en GitHub y protección de ramas

- **Contexto:** por decisión del equipo, en el repositorio trabajan solo el líder (JECR2005) y Claude. GitHub no
  permite aprobar un pull request propio, así que exigir una aprobación bloquearía toda integración.
- **Decisión:** `main` y `develop` exigen pull request y la integración continua («pruebas») en verde, prohíben
  reescribir o borrar el historial, y no exigen aprobaciones (0). El administrador puede saltar la regla en una
  emergencia. La revisión entre pares (Tabla 3.20) se cumple revisando cada PR antes de integrarlo.
- **Si se suman los compañeros:** `bash scripts/proteger_ramas.sh JECR2005/dogtor-veterinaria 1`.
- **Actualizar documento:** No.

## D-15 · Contraseñas simples solo en el entorno local (temporal)

- **Decisión:** `config/settings/local.py` deja vacía la lista `AUTH_PASSWORD_VALIDATORS`, para que durante las
  pruebas del sistema en la computadora del líder se usen contraseñas simples (la cuenta local `administrador`).
- **Alcance:** solo el entorno local. En `test`, `pruebas` y `produccion` siguen las reglas de RNF-01 (mínimo 10
  caracteres, no solo números, no comunes). Las contraseñas locales nunca se guardan en el repositorio.
- **Vigencia:** hasta el cierre de P5; se elimina en el endurecimiento (RNF-01, TS-03).
- **Actualizar documento:** No.

## D-16 · Una mascota no puede tener dos citas a la vez

- **Contexto:** RD-02 define el empalme por empleado. En la prueba exploratoria de UI-07 (DEF-001) se agendó a la
  misma mascota a la misma hora con dos veterinarios distintos, y el sistema lo aceptó.
- **Decisión:** además del empalme del empleado, el servicio de agenda rechaza una cita si la mascota ya tiene otra
  cita no cancelada que se traslape, con cualquier empleado. Mensaje: «La mascota ya tiene una cita a esa hora»,
  seguido del servicio, la hora y quién la atiende. La transacción bloquea al empleado y a la mascota.
- **Alcance:** agendar y reprogramar. Las citas canceladas no cuentan; terminar justo cuando otra empieza no es empalme.
- **Actualizar documento:** Sí. Agregar a RD-02 (Tabla 3.10) «una mascota no puede tener dos citas que se traslapen».

## D-17 · Cada rol ve solo la agenda de su puesto

- **Contexto:** la Tabla 4.9 da a Veterinario y Estilista acceso de consulta (○) a la Agenda, sin decir de quién.
  Al revisar P1, el líder pidió que el Veterinario no vea la agenda de todos.
- **Decisión:** Recepción y Administrador ven todas las citas. El Veterinario ve sus citas y las de los otros
  veterinarios; el Estilista, las suyas y las de los otros estilistas. Aplica al calendario, la lista del día, el
  detalle de la cita (404 si no le corresponde) y la lista de citas de la ficha de la mascota.
- **Dónde:** `agenda/services.py` (`puesto_visible`, `citas_visibles`, `empleados_visibles`).
- **Actualizar documento:** Sí. Agregar la nota a la Tabla 4.9 (Agenda: Veterinario y Estilista, solo su puesto).

## D-18 · PDF con xhtml2pdf en lugar de WeasyPrint

- **Contexto:** el apartado de componentes prevé WeasyPrint para los PDF de receta (RF-07), ticket y corte de caja
  (RF-13). En Windows, WeasyPrint necesita instalar aparte las bibliotecas gráficas GTK/Pango en cada equipo, lo que
  complica la instalación local (R10) y el script `scripts/instalar_local.ps1`.
- **Opciones:** (a) WeasyPrint con GTK; (b) xhtml2pdf, puro Python; (c) imprimir desde el navegador, que no cumple
  RF-07 porque el sistema no genera el PDF.
- **Decisión (19/11/2026, líder del proyecto):** opción **(b) xhtml2pdf 0.2.23** (Apache-2.0). Se instala con
  `pip` en Windows y en la integración continua, sin dependencias del sistema. Admite menos CSS que WeasyPrint,
  suficiente para documentos tamaño carta con tablas.
- **Dónde:** `requirements.txt`; `reportes/services.py` (`pdf_desde_html`, `pdf_desde_plantilla`) es la única
  puerta hacia la biblioteca, para poder cambiarla sin tocar las pantallas (R10).
- **Actualizar documento:** Sí. Tabla de componentes de terceros: «WeasyPrint» → «xhtml2pdf».


## D-19 · La base protege la consulta firmada (RD-07, RD-08)

- **Contexto:** al preparar S3-15 (pruebas que intentan violar las reglas) se vio que RD-07 y RD-08 solo los
  validaban el servicio y el modelo: un `QuerySet.update()`, un `create()` directo o SQL cambiaban una consulta
  firmada o le agregaban aplicaciones y recetas.
- **Decisión:** igual que RD-05 en S2-13, la base vuelve a exigir la regla:
  - CHECK con la función `fn_consulta_abierta` en `aplicacion`, `receta` y `detalle_receta`: solo se agregan a una
    consulta Abierta. Un CHECK no se vuelve a evaluar al firmar, así que lo ya capturado queda. En una base
    existente se agregan WITH NOCHECK, porque las aplicaciones de consultas ya firmadas son válidas (DEF-007).
  - `TR_consulta_firmada_solo_lectura` (AFTER UPDATE): si la consulta ya estaba firmada, regresa los valores y avisa
    con RAISERROR. No se usa INSTEAD OF UPDATE para no alterar el número de filas que Django espera al guardar.
  - `TR_consulta_firmada_no_se_borra` y `TR_aplicacion_de_consulta_firmada` (INSTEAD OF DELETE).
  - Puerta para P5: la corrección del Administrador con registro en la bitácora (RNF-03) pasará fijando
    `SESSION_CONTEXT('correccion_autorizada') = 1` en su transacción.
- **Dónde:** `bd/01_tablas.sql`, `bd/cambios/2026-11-19_RD-07_RD-08_consulta_firmada.sql`,
  `tests/integracion/test_S3_15_reglas_en_la_base.py`.
- **Actualizar documento:** Sí. Diccionario de datos (Tablas 3.42 a 3.45): anotar las restricciones nuevas.

## D-20 · Folio del ticket y cobro de lo aplicado en consulta

- **Contexto:** el diccionario define `venta.folio_ticket` (único) sin formato, y RD-09 pide que lo aplicado en
  una consulta no se descuente otra vez al cobrarlo (TI-05), sin decir con qué partida se cobra.
- **Opciones del folio:** (a) consecutivo por año `T-AAAA-NNNNN`, como la receta; (b) consecutivo simple;
  (c) por día. **Opciones del cobro:** (a) cada aplicación entra como servicio de la categoría Aplicación
  («Aplicación de vacuna», «Aplicación de desparasitante») a su precio de catálogo; (b) solo el servicio de la cita.
- **Decisión (20/11/2026, líder del proyecto):** folio **(a)** `T-2026-00001`, que reinicia cada año; cobro **(a)**.
  Un ticket que se arma desde una cita propone el servicio de la cita y una partida de servicio por cada aplicación;
  la recepcionista puede quitar partidas antes de generarlo. Las partidas de servicio no tocan el inventario: el
  lote ya bajó al aplicar (RD-09) y al cancelar el ticket no se reintegra (RF-14).
- **Dónde:** `ventas/services.py` (`siguiente_folio`); el armado del ticket desde la cita, en S4-05.
- **Actualizar documento:** Sí. Tabla 3.54: formato del folio. RD-09: anotar con qué partida se cobra lo aplicado.

## D-21 · La base protege las ventas (RD-06, RD-11, RD-12, RF-14)

- **Contexto:** al preparar S4-16 se revisó qué reglas de Ventas protegía solo el servicio. Los CHECK del diccionario
  ya impiden un saldo negativo o mayor que el total, «Pagada» con saldo, un cambio que no cuadra y una cancelación
  sin motivo (RD-06, RF-14). Pero un `QuerySet.update()`, un `create()` directo o SQL podían cambiar el precio de
  una línea (RD-11), vender un medicamento con control sin su receta (RD-12), modificar o borrar un pago y
  reactivar un ticket cancelado.
- **Decisión:** igual que D-19 en P3, la base vuelve a exigir esas reglas:
  - CHECK `CK_detalle_venta_receta_valida` con la función `fn_linea_con_receta_valida`: si el producto requiere
    receta, la línea lleva una receta que lo incluye. Que la receta sea de una mascota del mismo cliente lo
    valida el servicio.
  - `TR_detalle_venta_precio_historico` (INSTEAD OF UPDATE): las líneas no cambian. No hay INSTEAD OF DELETE
    porque SQL Server no lo permite en una tabla con borrado en cascada desde `venta`.
  - `TR_pago_inmutable` (INSTEAD OF UPDATE, DELETE): lo devuelto se registra como pago «Devolución».
  - `TR_venta_cancelada_solo_lectura` (AFTER UPDATE): regresa los valores de un ticket cancelado y avisa, igual que
    la consulta firmada (D-19).
- **Dónde:** `bd/01_tablas.sql`, `bd/cambios/2026-11-20_RD-06_RD-11_RD-12_ventas.sql`,
  `tests/integracion/test_S4_16_reglas_en_la_base.py`.
- **Actualizar documento:** Sí. Diccionario de datos (Tablas 3.54 a 3.56): anotar las restricciones nuevas.

## D-22 · Herramientas, entorno con https y medición de la disponibilidad en P5

- **Contexto:** la Tabla 4.15 pide Playwright (TS-01, TS-04), OWASP ZAP (TS-02) y Locust (TS-06); TS-03 pide https
  en el servidor de producción de la Tabla 4.2 (Linux, Nginx y Gunicorn), que todavía no existe en el local; TS-08
  pide un mes de monitoreo externo y el Sprint 5 dura dos semanas (20/11 al 3/12/2026, con la entrega académica
  el 1/12). Además, TS-05 y TS-06 piden más de 1,000 mascotas con historia, sin romper los escenarios de P1 a P4.
- **Decisión (21/11/2026, líder del proyecto):**
  - **Herramientas:** las tres de la Tabla 4.15. Playwright y Locust entran al repositorio
    (`requirements-dev.txt`, `tests/sistema/`); OWASP ZAP se ejecuta en la laptop con su imagen de Docker, en
    modo de escaneo base, contra el entorno con https.
  - **Entorno con https:** Docker Desktop en la laptop de JECR2005 hace de servidor del local: un contenedor con
    Gunicorn y `config.settings.produccion` y otro con Nginx y un certificado local, conectados al SQL Server
    instalado en la laptop. Se respeta la Tabla 4.2 (Linux, Nginx, Gunicorn); solo cambia el certificado, que es
    local en lugar de uno emitido por una autoridad pública, porque el local todavía no tiene dominio.
  - **TS-08 en periodo reducido:** un monitor programado, fuera de la aplicación, consulta `/salud/` cada 5 minutos
    de lunes a sábado de 9:00 a 19:00 mientras el servidor está encendido, desde que el entorno queda listo hasta el
    cierre del sprint. El reporte da el porcentaje de caídas sobre las horas monitoreadas. El mes completo queda
    como seguimiento en operación después de `v1.0`.
  - **Datos de volumen:** `cargar_datos_prueba --mascotas 1200 --historial 30` agrega 30 días de consultas firmadas
    y tickets pagados (8 por día hábil) a mascotas que no son de los escenarios. Esos tickets llevan el folio
    `H-AAAAMMDD-NN` (histórico ficticio) para no tomar números de la serie `T-AAAA-NNNNN` (D-20): el siguiente
    ticket de hoy sigue siendo `T-AAAA-00003`, como esperan los guiones. No crean aplicaciones ni venden productos,
    así que no cambian existencias, recordatorios, alertas ni avisos.
- **Impacto:** TS-08 se reporta como medición parcial; su criterio (caídas menores al 1 % de las horas laborales)
  se evalúa sobre el periodo medido. Los guiones de P1 a P4 se siguen ejecutando con la carga por defecto.
- **Dónde:** `catalogos/management/commands/cargar_datos_prueba.py` (`--historial`),
  `tests/integracion/test_S5_03_datos_de_volumen.py`; el entorno con Docker, el monitor y las herramientas, en
  los bloques C, D y E del Sprint 5.
- **Actualizar documento:** Sí. Tabla 4.15 (TS-08: periodo reducido; TS-03: certificado local), apartado 4.6.1
  (instalación y despliegue con Docker en el equipo del local) y Tabla 4.2 (nota del certificado).

## D-23 · Qué registra la bitácora y cómo se protege (RNF-03, RNF-08)

- **Contexto:** hasta P4 la bitácora solo registraba bajas de clientes, reactivaciones de cuentas y cancelaciones
  de tickets. S5-04 pide los cambios en ventas, consultas, recetas e inventario, y S5-05 a S5-07, la consulta,
  las exportaciones y la corrección de consultas firmadas. La tabla (Tabla 3.57) no tiene columna para el motivo
  ni para lo exportado, y una exportación no tiene un registro al que apuntar.
- **Decisión:**
  - **Qué se registra** (la cuenta que lo hizo, la fecha y los valores previos cuando el registro ya existía):

    | Componente | Alta | Modificación (con valores previos) | Cancelación (con valores previos) |
    |---|---|---|---|
    | Consultas | abrir la consulta | guardar cambios (solo si algo cambió), firmar, corrección del Administrador | — |
    | Aplicaciones y recetas | aplicación, receta emitida, atención de estética | — | quitar una aplicación |
    | Inventario y compras | entrada de mercancía, pedido | ajuste de un lote, cambio y recepción del pedido | cancelar un pedido |
    | Ventas | ticket, pago (cobro) | marca «Requiere factura» | cancelar un ticket (desde P4) |

    Las salidas de inventario por venta o aplicación no llevan registro propio: las registra la operación que las
    provoca (el ticket o la aplicación).
  - **Quién:** los servicios reciben a la cuenta o al empleado; la bitácora guarda la cuenta del empleado. Un
    empleado sin cuenta no puede hacer cambios (toda acción la hace una cuenta, Tabla 3.38).
  - **Motivo de una corrección:** va dentro de los valores previos con la clave `motivo_de_la_correccion`. La
    corrección abre la puerta de D-19 (`SESSION_CONTEXT('correccion_autorizada') = 1`) solo durante el cambio y
    la cierra al terminar, aunque falle. Si cambia el peso y es la consulta firmada más reciente, también se
    corrige el peso actual de la mascota.
  - **Exportaciones** (de la bitácora y de contactos): acción «Exportación», `id_registro` 0 y, en lugar de
    valores previos, los filtros y el número de filas exportadas. Se piden con POST porque dejan registro; la de
    contactos pide confirmar que se usarán solo para las finalidades del aviso de privacidad (LFPDPPP) y excluye a
    los clientes dados de baja.
  - **La base protege la bitácora:** `TR_bitacora_inmutable` (INSTEAD OF UPDATE, DELETE) rechaza cualquier
    cambio, e `IX_bitacora_usuario_fecha` acelera el filtro por usuario de UI-20.
- **Dónde:** `seguridad/bitacora.py`, `seguridad/views_bitacora.py` (UI-20), los servicios de `clinico`,
  `inventario` y `ventas`, `bd/01_tablas.sql` y `bd/cambios/2026-11-21_RNF-03_bitacora_inmutable.sql`.
- **Actualizar documento:** Sí. Tabla 3.57 (uso de `valores_previos` en exportaciones y correcciones, el disparador
  y el índice), apartado 4.4 (UI-20) y el diccionario de datos con la nota del disparador.

## D-24 · Tareas programadas y servidor limpio para TS-07

- **Contexto:** RNF-04 pide un respaldo diario fuera del horario con copia externa y 30 días de conservación, y
  TS-07 pide restaurar el respaldo del día «en un servidor limpio» comparando el número de registros. RF-09 pide
  la lista de recordatorios lista al abrir, y TS-08 (D-22), un monitor en horario. La laptop de JECR2005 tiene
  SQL Server 2025 (instancia predeterminada) y no hay un segundo servidor.
- **Decisión:**
  - **Tareas:** `scripts/programar_tareas.ps1` crea tres tareas en la carpeta «Dogtor» del Programador de tareas,
    con la cuenta de Windows de quien la ejecuta, sin ventana (`pythonw.exe` y `scripts/tarea.py`): respaldo a
    las 22:00 todos los días; recordatorios a las 08:30 de lunes a sábado; monitor cada 5 min de 9:00 a 19:00 de
    lunes a sábado. El respaldo y los recordatorios se ejecutan al encender el equipo si estaba apagado a su
    hora. Cada ejecución queda en `logs/tareas.log` (fuera del repositorio).
  - **Servidor limpio:** un contenedor de SQL Server 2025 Developer (`docker/servidor_limpio.yml`) sin volumen de
    datos: arranca vacío cada vez y lee los respaldos de `RESPALDO_DIR` en solo lectura. Tiene que ser 2025 o
    posterior, porque un respaldo no se restaura en una versión anterior. `respaldo.py ts07` respalda en ese
    momento, restaura en el contenedor, ejecuta `DBCC CHECKDB` y compara `COUNT_BIG(*)` de cada tabla.
  - La contraseña del usuario `sa` del contenedor la elige JECR2005 en `.env` (`RESTAURACION_CONTRASENA`); no
    se guarda en el repositorio.
- **Dónde:** `scripts/programar_tareas.ps1`, `scripts/tarea.py`, `scripts/monitor.py`, `scripts/respaldo.py`
  (`ts07`), `docker/servidor_limpio.yml`, `.env.example`, `tests/unidad/test_S5_08_tareas_respaldo_y_monitor.py`.
- **Actualizar documento:** Sí. Tabla 4.28 (tareas de respaldo y recordatorios con su hora), apartado 4.6.1
  (comandos de respaldo y restauración) y Tabla 4.15 (TS-07: servidor limpio en contenedor).
