# Cambios al documento del proyecto (S5-22)

> Lista de lo que hay que cambiar en el documento Word («Indice GPS») para que describa el sistema como quedó.
> Sale de las decisiones D-01 a D-27 (`docs/decisiones.md`) con «Actualizar documento: Sí» u «Opcional», revisadas
> contra el texto actual del documento. Está en el orden del documento. Marque ☑ cada cambio al aplicarlo.
> **Dice** copia lo que el documento tiene hoy; **Debe decir** es el texto propuesto.

## Capítulo 3

### 3.1 · Requisitos: Tabla 3.10, reglas de dominio

| ☐ | Dónde | Dice | Debe decir | Decisión |
|---|---|---|---|---|
| ☐ | RD-02, columna de descripción | «Una cita debe caer dentro del horario laboral del empleado y no puede empalmarse con otra cita activa del mismo empleado.» | «… del mismo empleado. **Una mascota tampoco puede tener dos citas que se traslapen, con cualquier empleado.**» | D-16 |
| ☐ | RD-09, columna de descripción | «… y se cobran mediante un servicio del catálogo cuya línea no descuenta stock …» | «… y se cobran mediante un servicio del catálogo de la categoría Aplicación («Aplicación de vacuna», «Aplicación de desparasitante»), cuya línea no descuenta stock; el ticket que se arma desde la cita propone una línea por cada aplicación …» | D-20 |

### 3.2.3 · Riesgos: plan de respuesta de R07

| ☐ | Dónde | Dice | Debe decir | Decisión |
|---|---|---|---|---|
| ☐ | R07, acciones | «… impresión de la agenda del día al abrir.» | «… la agenda del día sale en PDF tamaño carta (alergias, teléfono y casillas para anotar lo atendido, lo aplicado y lo cobrado); la tarea programada la deja a las 08:35 en la laptop y se imprime desde la agenda del día. Si solo falla el internet, el sistema sigue funcionando en la red del local.» | D-27 |
| ☐ | R07, contingencia | «Atender con la agenda impresa del día y capturar al restablecerse el servicio.» | «… y capturar el mismo día al restablecerse el servicio: el veterinario captura y firma las consultas, el estilista registra las atenciones y Recepción cobra desde «Por cobrar hoy»; el corte de caja se compara con lo anotado.» | D-27 |

### 3.5 · Diccionario de datos

| ☐ | Dónde | Dice | Debe decir | Decisión |
|---|---|---|---|---|
| ☐ | Convención «Tipos» | Tipos del estándar SQL (VARCHAR, CHAR, TEXT, DATETIME, BOOLEAN) | Agregar al final: «En SQL Server se implementan como VARCHAR(n) → NVARCHAR(n), CHAR(n) → NCHAR(n), TEXT → NVARCHAR(MAX), DATETIME → DATETIME2 y BOOLEAN → BIT; INT, SMALLINT, DECIMAL(p,s), DATE y TIME se conservan. Las fechas y horas se guardan en UTC y se muestran en hora de Tampico.» | D-11 |
| ☐ | Tabla 3.42 CONSULTA, nota bajo la tabla | — | «Una consulta Firmada no se modifica ni se borra: la base regresa los cambios (`TR_consulta_firmada_solo_lectura`) y rechaza el borrado (`TR_consulta_firmada_no_se_borra`). Solo la corrección del Administrador pasa, con motivo y registro en la bitácora (RD-07, RNF-03).» | D-19, D-23 |
| ☐ | Tablas 3.43 APLICACION y 3.44 RECETA, nota | — | «Solo se agregan a una consulta Abierta (CHECK con la función `fn_consulta_abierta`); una aplicación de una consulta firmada no se borra (`TR_aplicacion_de_consulta_firmada`) (RD-07, RD-08).» | D-19 |
| ☐ | Tabla 3.45 DETALLE_RECETA | `id_receta` PK, FK · `id_producto` PK, FK | Nueva primera fila `id_detalle_receta · INT · No · PK · Identificador.`; `id_receta` FK y `id_producto` FK, marcadas **UK** en conjunto («no se repite un medicamento en la receta»). Nota: «Solo se agrega a una receta de una consulta Abierta (D-19).» | D-01, D-19 |
| ☐ | Tabla 3.49 LOTE | `cantidad_disponible · INT` | `cantidad_disponible · DECIMAL(10,2)` («existencias con decimales para productos que se aplican por mL») | D-04 |
| ☐ | Tabla 3.50 MOVIMIENTO_INVENTARIO | `cantidad · INT` | `cantidad · DECIMAL(10,2)`. Nota: «La base no deja modificar ni borrar un movimiento (`TR_movimiento_inventario_inmutable`); un error se corrige con un Ajuste.» | D-04, D-13 |
| ☐ | Tabla 3.53 DETALLE_PEDIDO | `id_pedido` PK, FK · `id_producto` PK, FK | Nueva primera fila `id_detalle_pedido · INT · No · PK · Identificador.`; `id_pedido` + `id_producto` como **UK** | D-01 |
| ☐ | Tabla 3.54 VENTA | `folio_ticket` «Folio consecutivo del ticket.» | «Folio consecutivo por año, `T-AAAA-NNNNN` (por ejemplo T-2026-00001), que reinicia cada año.» Nota: «Un ticket Cancelado ya no cambia: la base regresa los valores (`TR_venta_cancelada_solo_lectura`).» | D-20, D-21 |
| ☐ | Tabla 3.55 DETALLE_VENTA | `id_venta` PK, FK · `numero_linea` PK | Nueva primera fila `id_detalle_venta · INT · No · PK · Identificador.`; `id_venta` + `numero_linea` como **UK**. Nota: «Las líneas no se modifican (`TR_detalle_venta_precio_historico`, RD-11) y un producto con control lleva una receta que lo incluye (`CK_detalle_venta_receta_valida`, RD-12).» | D-01, D-21 |
| ☐ | Tabla 3.56 PAGO, nota | — | «Un pago no se modifica ni se borra (`TR_pago_inmutable`); lo devuelto se registra como pago de tipo Devolución.» | D-21 |
| ☐ | Tabla 3.57 BITACORA_AUDITORIA, `valores_previos` | «Valores antes del cambio.» | «Valores antes del cambio, en JSON. En una corrección de consulta incluye el motivo; en una exportación guarda los filtros y el número de filas (con `id_registro` 0).» Nota: «La base no deja modificar ni borrar la bitácora (`TR_bitacora_inmutable`); el índice `IX_bitacora_usuario_fecha` acelera el filtro por usuario.» | D-23 |

## Capítulo 4

### 4.1 · Tabla 4.2, plataforma tecnológica

| ☐ | Fila | Dice | Debe decir | Decisión |
|---|---|---|---|---|
| ☐ | Lenguaje y framework web | Python y Django | Python 3.12 y Django 5.2 (LTS) | D-06 (opcional) |
| ☐ | Base de datos | PostgreSQL | Microsoft SQL Server (2022 Express en el local, 2025 en la laptop del equipo) con `mssql-django` y ODBC Driver 18; el esquema se programa en T-SQL | D-09, D-10 |
| ☐ | Documentos | WeasyPrint | xhtml2pdf (Apache-2.0): se instala con pip en Windows, sin bibliotecas gráficas aparte | D-18 |
| ☐ | Tareas programadas | Comandos de gestión de Django ejecutados con cron del servidor | Programador de tareas de Windows con `scripts/tarea.py` (respaldo, recordatorios, agenda del día y monitor) | D-09, D-24 |
| ☐ | Servidor y despliegue | Linux con Gunicorn, Nginx y certificado TLS | Docker Desktop en el equipo del local con contenedores Linux de Nginx (TLS 1.2/1.3) y Gunicorn; dominio `dogtor.local` y certificado local de mkcert, porque el local todavía no tiene dominio público | D-22, D-25 |
| ☐ | Respaldo y monitoreo | pg_dump programado … y monitoreo externo de disponibilidad | `BACKUP DATABASE` con CHECKSUM y `RESTORE VERIFYONLY`, copia externa (OneDrive) y 30 días; monitor programado de `/salud/` cada 5 min en horario | D-09, D-22, D-24 |
| ☐ | Justificación de la base (texto bajo la tabla, criterio de costo) | Se eligió PostgreSQL | SQL Server Express es gratuito, limita cada base a 10 GB (suficiente para una clínica) y no trae Agente SQL, por eso las tareas van en el Programador de tareas de Windows | D-09 |

### 4.4 · Menú y pantallas

| ☐ | Dónde | Cambio | Decisión |
|---|---|---|---|
| ☐ | Tabla 4.9, fila Agenda | Nota: «El Veterinario ve las citas de los veterinarios y el Estilista las de los estilistas; Recepción y Administrador ven todas.» | D-17 |
| ☐ | UI-20 Bitácora y exportación | Agregar: «Filtros por fecha, usuario, acción y entidad; valores previos de cada registro; exportación en CSV de lo filtrado y de contactos (sin clientes dados de baja, con confirmación del aviso de privacidad); cada exportación queda en la bitácora.» | D-23 |

### 4.5.2.4 · Tabla 4.15, casos de prueba de sistema (columna «Método y herramienta»)

| ☐ | Caso | Debe decir | Decisión |
|---|---|---|---|
| ☐ | TS-01 | «Abrir por dirección directa **todas** las rutas del sistema con los cuatro roles y sin sesión (prueba automática con el cliente de pruebas de Django, 560 combinaciones)» | Implementación de S1-20 y S5-17 |
| ☐ | TS-02 | «Pruebas automáticas con texto malicioso en filtros y formularios con sesión, y OWASP ZAP (escaneo completo sin sesión) contra el entorno https» | D-25 |
| ☐ | TS-03 | Agregar: «… en https://dogtor.local con certificado local de mkcert; `check --deploy` sin avisos y cabeceras de seguridad revisadas» | D-22, D-25 |
| ☐ | TS-04 | «Playwright en Chrome y Edge instalados y en una Galaxy Tab S4 emulada (10.5", horizontal, táctil); los PDF miden 612 × 792 pt y se imprimen a mano en carta» | D-27 |
| ☐ | TS-05 | «… en https://dogtor.local con 1,200 mascotas; la integración continua repite la medición con 1,050» | D-26 |
| ☐ | TS-06 | «Locust con 5 recepcionistas que generan y cobran tickets y 5 veterinarios que guardan consultas, durante 30 min; se cuenta el porcentaje exacto de operaciones en 2 s o menos» | D-26 |
| ☐ | TS-07 | «… en un servidor limpio: SQL Server 2025 en un contenedor de Docker sin datos (`respaldo.py ts07`), con DBCC CHECKDB y el conteo de cada tabla» | D-24 |
| ☐ | TS-08 | «Monitor programado de `/salud/` cada 5 min de lunes a sábado de 9:00 a 19:00, en **periodo reducido** durante el Sprint 5; el mes completo continúa en operación» | D-22 |
| ☐ | TS-11 | «Agenda del día en PDF (tarea de las 08:35 o botón de la agenda); se atiende con la hoja y se recaptura el mismo día con las pantallas normales» | D-27 |

### 4.6.1 · Guía técnica

| ☐ | Dónde | Dice | Debe decir | Decisión |
|---|---|---|---|---|
| ☐ | Tabla 4.23, vista Física | «… Gunicorn con Django, PostgreSQL y copia de respaldo externa» | «Navegador del local, Nginx con TLS y Gunicorn con Django en Docker, SQL Server en el mismo equipo y copia de respaldo externa» | D-09, D-25 |
| ☐ | Recorrido de una solicitud | «Django lee y escribe en PostgreSQL …» · «Tareas programadas del servidor …» | «Django lee y escribe en SQL Server con la cuenta `dogtor_web` (solo lectura y escritura de datos) …» · «El Programador de tareas de Windows genera los recordatorios, la agenda impresa y los respaldos …» | D-09, D-24, D-25 |
| ☐ | Tabla 4.25, Servidor | «Linux con soporte vigente, 2 vCPU, 4 GB …» | «Equipo del local con Windows 10 u 11 y Docker Desktop (contenedores Linux); en P5 lo hace la laptop del equipo» | D-22 |
| ☐ | Tabla 4.25, Software del servidor | «Python, PostgreSQL, Nginx, Gunicorn y Git …» | «Python 3.12, SQL Server Express, ODBC Driver 18, Docker Desktop (Nginx y Gunicorn en contenedores), mkcert y Git» | D-09, D-25 |
| ☐ | Base de datos, primer punto | «… se implementa con las migraciones de Django …» | «… se implementa con los scripts de `bd/` (`01_tablas.sql`, `02_vistas.sql`); los modelos usan las tablas con `managed = False` y cada cambio de esquema lleva su script en `bd/cambios/`.» | D-10 |
| ☐ | Base de datos, restricciones | (lista actual) | Agregar: los CHECK adicionales (D-03) y los disparadores de D-13, D-19, D-21 y D-23; la unicidad de campos opcionales con índice filtrado (D-12). | D-03 (opcional), D-12, D-13, D-19, D-21, D-23 |
| ☐ | Tabla 4.26, Bitácora | «Registro automático de cambios …» | Agregar: «… con los valores previos; la base no permite modificarla ni borrarla» | D-23 |
| ☐ | Tabla 4.26, Secretos | «Claves y datos de conexión en variables de entorno …» | «… en `.env` (desarrollo) y `docker/produccion.env` (producción, generado al azar en el equipo y nunca en el repositorio); la base se usa con la cuenta `dogtor_web` de privilegio mínimo» | D-25 |
| ☐ | Tabla 4.26, nueva fila «Cabeceras de seguridad» | — | «HSTS, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` y política de contenido del propio sitio; cookies seguras y de solo servidor · RNF-01» | D-25 |
| ☐ | Tabla 4.26, Dependencias | «Versiones fijas y revisión periódica …» | «Versiones fijas y `pip-audit` en cada integración continua» | D-25 |
| ☐ | Tabla 4.27, columna «En la base de datos» | RD-02 «Opcional: restricción de exclusión …» · RD-06 «Validación en la transacción …» · RD-07 «Los movimientos … no se borran …» · RD-08 «La consulta es obligatoria …» · RD-11 «Precio unitario guardado …» · RD-12 «La receta de respaldo es una referencia …» | RD-02: «Bloqueo de las filas del empleado y de la mascota al agendar» (D-16) · RD-06: «CHECK de saldo y cambio, y pagos inmutables» · RD-07: «Disparadores que impiden cambiar movimientos y consultas firmadas» · RD-08: «CHECK `fn_consulta_abierta`» · RD-11: «Disparador que impide cambiar la línea» · RD-12: «CHECK `CK_detalle_venta_receta_valida`» | D-13, D-16, D-19, D-21 |
| ☐ | Tabla 4.28, Generar recordatorios | «Diaria, antes de abrir (8:00 h)» | «Lunes a sábado a las 08:30 (Programador de tareas; si el equipo estaba apagado, al encenderlo)» | D-24 |
| ☐ | Tabla 4.28, Respaldo | «… envío a almacenamiento externo …» | «… a las 22:00 todos los días: BACKUP con CHECKSUM y verificación, copia en OneDrive y borrado de respaldos con más de 30 días» | D-09, D-24 |
| ☐ | Tabla 4.28, nuevas filas | — | «Agenda del día · lunes a sábado 08:35 · deja el PDF de la agenda para la contingencia · R07» y «Monitor de disponibilidad · cada 5 min de 9:00 a 19:00, lunes a sábado · revisa `/salud/` y registra caídas · RNF-06» | D-24, D-27 |
| ☐ | Tabla 4.28, Prueba de restauración | «Restaura el respaldo en un servidor limpio …» | Agregar: «… (contenedor de SQL Server 2025 con `respaldo.py ts07`)» | D-24 |
| ☐ | Instalación y despliegue | Pasos con `source .venv/bin/activate`, `migrate`, `createsuperuser`, Gunicorn como servicio, firewall | Pasos de Windows: `preparar_equipo.ps1` o `instalar_local.ps1`; `python bd/ejecutar.py` para crear las tablas; `python manage.py migrate` (solo las tablas de Django) y la cuenta inicial; `preparar_produccion.ps1` para el entorno https; `programar_tareas.ps1` para las tareas (README del repositorio) | D-09, D-10, D-22, D-25 |
| ☐ | Respaldo y restauración | `pg_dump -Fc …` · `createdb …` · `pg_restore …` | `python scripts/respaldo.py respaldar` · `python scripts/respaldo.py restaurar ARCHIVO.bak --base NOMBRE` · `python scripts/respaldo.py ts07` (servidor limpio) | D-09, D-24 |
| ☐ | Tabla 4.29, «El sistema no responde» | «Revisar Nginx, Gunicorn y PostgreSQL …» | «Revisar `docker compose ps` y `docker compose logs`, y que el servicio de SQL Server esté iniciado; …» | D-09, D-25 |
| ☐ | Tabla 4.29, «No aparecen los recordatorios» | «… revisar la configuración de cron» | «… revisar la tarea en el Programador de tareas (carpeta Dogtor) y `logs\tareas.log`» | D-24 |

### 4.6.2 · Guía de usuario

| ☐ | Dónde | Cambio | Decisión |
|---|---|---|---|
| ☐ | Capacitación inicial | Mencionar la guía de 30 minutos (`docs/gestion/guia_capacitacion.md`) y la Ayuda dentro del sistema por rol | S5-18 |
| ☐ | Recepción | Agregar «Si se va la luz o la red»: imprimir la agenda (contingencia) y recapturar el mismo día | D-27 |

## Resultados (se llenan con los documentos de `docs/gestion/`)

| ☐ | Dónde | De dónde se toma |
|---|---|---|
| ☐ | Tabla 4.20 (resumen por prototipo) | `resultados_pruebas.md`; P5 se completa después de TA-09 y TA-10 |
| ☐ | Capítulo 5, resultados y conclusiones | `evaluacion_P1.md` a `evaluacion_P5.md`, actas de aceptación, `riesgos.md` y los defectos DEF-001 a DEF-008 |

Las decisiones con «Actualizar documento: No» (D-02, D-05, D-07, D-08, D-14, D-15) no cambian el documento.
