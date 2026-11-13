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

## D-04 · Cantidad decimal en aplicación contra existencias enteras (observación abierta)

- **Contexto:** `aplicacion.cantidad` es DECIMAL(8,2), pero `lote.cantidad_disponible` y
  `movimiento_inventario.cantidad` son INT. Aplicar 0.5 mL de un frasco no puede descontarse de un lote entero.
- **Decisión:** se respeta el diccionario en Sprint 0. **Se decide en P2**, antes de programar RD-05 y RD-09, entre:
  (a) contar las existencias en la unidad mínima (mL, tabletas) para que todo sea entero, o
  (b) cambiar las existencias y los movimientos a DECIMAL.
- **Responsable:** responsable de base de datos con el desarrollador clínico.
- **Actualizar documento:** Sí, cuando se tome la decisión (Tablas 3.43, 3.49 y 3.50).

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
