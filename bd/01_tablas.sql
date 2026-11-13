/* =============================================================================
   Dogtor: Veterinaria & Petcare · Sistema de gestión
   01 · Tablas del modelo de datos (apartados 3.4 y 3.5) para SQL Server 2016 o posterior

   Fuente única del esquema (decisión D-10): Django solo usa estas tablas (managed = False).
   Ejecutar conectado a la base Dogtor:
       sqlcmd -S localhost\SQLEXPRESS -E -C -d Dogtor -i bd\01_tablas.sql
   o abrirlo en SSMS con la base Dogtor seleccionada y pulsar Ejecutar.

   Contenido: 26 tablas con llaves primarias, foráneas y únicas, restricciones CHECK de los
   valores permitidos y de las reglas de dominio, valores por defecto e índices (RNF-05).
   Todo se crea en una sola transacción: si algo falla, no queda ninguna tabla a medias.

   Equivalencias con el diccionario (decisión D-11):
       VARCHAR(n) → NVARCHAR(n)     CHAR(n) → NCHAR(n)     TEXT → NVARCHAR(MAX)
       DATETIME   → DATETIME2       BOOLEAN → BIT          INT, SMALLINT, DECIMAL, DATE, TIME igual
   Las fechas y horas (DATETIME2) se guardan en UTC; Django las muestra en hora de Tampico.
   ============================================================================= */

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;   -- requerido por los índices filtrados
GO

SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.cliente', N'U') IS NOT NULL
    THROW 50000, N'Las tablas de Dogtor ya existen. En desarrollo, ejecute primero bd\99_borrar_tablas.sql.', 1;

/* ---------------------------------------------------------------------------
   Bloque A1 · Clientes y mascotas
   --------------------------------------------------------------------------- */

-- Tabla 3.33 · ESPECIE
CREATE TABLE dbo.especie (
    id_especie  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_especie PRIMARY KEY,
    nombre      NVARCHAR(40)      NOT NULL CONSTRAINT UQ_especie_nombre UNIQUE
);

-- Tabla 3.34 · RAZA
CREATE TABLE dbo.raza (
    id_raza     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_raza PRIMARY KEY,
    id_especie  INT               NOT NULL CONSTRAINT FK_raza_especie REFERENCES dbo.especie (id_especie),
    nombre      NVARCHAR(60)      NOT NULL
);

-- Tabla 3.32 · CLIENTE (RF-01)
CREATE TABLE dbo.cliente (
    id_cliente               INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_cliente PRIMARY KEY,
    nombre                   NVARCHAR(60)  NOT NULL,
    apellido_paterno         NVARCHAR(40)  NOT NULL,
    apellido_materno         NVARCHAR(40)  NULL,
    telefono                 NVARCHAR(15)  NOT NULL,
    correo                   NVARCHAR(100) NULL,
    direccion                NVARCHAR(150) NULL,
    preferencia_contacto     NVARCHAR(15)  NOT NULL
        CONSTRAINT CK_cliente_preferencia_contacto CHECK (preferencia_contacto IN (N'Teléfono', N'WhatsApp', N'Correo')),
    rfc                      NVARCHAR(13)  NULL,
    razon_social_fiscal      NVARCHAR(120) NULL,
    regimen_fiscal           NVARCHAR(5)   NULL,
    cp_fiscal                NCHAR(5)      NULL,
    -- RF-01 y RNF-08: no se guarda un cliente sin aceptación del aviso de privacidad
    acepto_aviso_privacidad  BIT           NOT NULL
        CONSTRAINT CK_cliente_acepta_aviso CHECK (acepto_aviso_privacidad = 1),
    fecha_registro           DATETIME2     NOT NULL CONSTRAINT DF_cliente_fecha_registro DEFAULT SYSUTCDATETIME(),
    activo                   BIT           NOT NULL CONSTRAINT DF_cliente_activo DEFAULT 1
);
CREATE INDEX IX_cliente_telefono ON dbo.cliente (telefono);   -- RNF-05: búsqueda por teléfono

-- Tabla 3.35 · MASCOTA (RF-02)
CREATE TABLE dbo.mascota (
    id_mascota        INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_mascota PRIMARY KEY,
    id_cliente        INT           NOT NULL CONSTRAINT FK_mascota_cliente REFERENCES dbo.cliente (id_cliente),
    id_raza           INT           NOT NULL CONSTRAINT FK_mascota_raza REFERENCES dbo.raza (id_raza),
    nombre            NVARCHAR(40)  NOT NULL,
    sexo              NCHAR(1)      NOT NULL CONSTRAINT CK_mascota_sexo CHECK (sexo IN (N'M', N'H')),
    fecha_nacimiento  DATE          NULL,
    peso_actual       DECIMAL(5,2)  NULL CONSTRAINT CK_mascota_peso CHECK (peso_actual IS NULL OR peso_actual > 0),
    color             NVARCHAR(40)  NULL,
    esterilizado      BIT           NOT NULL CONSTRAINT DF_mascota_esterilizado DEFAULT 0,
    estatus           NVARCHAR(10)  NOT NULL CONSTRAINT DF_mascota_estatus DEFAULT N'Activa'
        CONSTRAINT CK_mascota_estatus CHECK (estatus IN (N'Activa', N'Inactiva', N'Fallecida'))
);
CREATE INDEX IX_mascota_cliente ON dbo.mascota (id_cliente);   -- RNF-05: mascotas de un cliente

/* ---------------------------------------------------------------------------
   Bloque A2 · Personal, servicios, agenda y auditoría
   --------------------------------------------------------------------------- */

-- Tabla 3.36 · EMPLEADO (RF-03)
CREATE TABLE dbo.empleado (
    id_empleado         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_empleado PRIMARY KEY,
    nombre              NVARCHAR(60) NOT NULL,
    apellidos           NVARCHAR(80) NOT NULL,
    puesto              NVARCHAR(15) NOT NULL
        CONSTRAINT CK_empleado_puesto CHECK (puesto IN (N'Veterinario', N'Estilista', N'Recepcionista', N'Administrador')),
    cedula_profesional  NVARCHAR(12) NULL,
    telefono            NVARCHAR(15) NULL,
    fecha_ingreso       DATE         NOT NULL,
    activo              BIT          NOT NULL CONSTRAINT DF_empleado_activo DEFAULT 1,
    -- RF-03 y RD-01: la cédula profesional es obligatoria para el puesto Veterinario
    CONSTRAINT CK_empleado_veterinario_cedula
        CHECK (puesto <> N'Veterinario' OR (cedula_profesional IS NOT NULL AND cedula_profesional <> N''))
);
-- UK de la cédula: índice filtrado porque una UNIQUE normal de SQL Server admite un solo NULL (D-12)
CREATE UNIQUE INDEX UX_empleado_cedula ON dbo.empleado (cedula_profesional) WHERE cedula_profesional IS NOT NULL;

-- Tabla 3.37 · HORARIO_LABORAL (RD-02)
CREATE TABLE dbo.horario_laboral (
    id_horario    INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_horario_laboral PRIMARY KEY,
    id_empleado   INT      NOT NULL CONSTRAINT FK_horario_empleado REFERENCES dbo.empleado (id_empleado) ON DELETE CASCADE,
    dia_semana    SMALLINT NOT NULL CONSTRAINT CK_horario_dia_semana CHECK (dia_semana BETWEEN 1 AND 6),
    hora_entrada  TIME(0)  NOT NULL,
    hora_salida   TIME(0)  NOT NULL,
    CONSTRAINT CK_horario_salida_mayor CHECK (hora_salida > hora_entrada)
);
CREATE INDEX IX_horario_empleado ON dbo.horario_laboral (id_empleado, dia_semana);

-- Tabla 3.38 · USUARIO (RNF-01)
CREATE TABLE dbo.usuario (
    id_usuario         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_usuario PRIMARY KEY,
    id_empleado        INT           NOT NULL CONSTRAINT FK_usuario_empleado REFERENCES dbo.empleado (id_empleado)
                                              CONSTRAINT UQ_usuario_empleado UNIQUE,
    nombre_usuario     NVARCHAR(30)  NOT NULL CONSTRAINT UQ_usuario_nombre_usuario UNIQUE,
    hash_contrasena    NVARCHAR(255) NOT NULL,   -- hash con sal; nunca texto plano
    rol                NVARCHAR(15)  NOT NULL
        CONSTRAINT CK_usuario_rol CHECK (rol IN (N'Administrador', N'Veterinario', N'Estilista', N'Recepcionista')),
    activo             BIT           NOT NULL CONSTRAINT DF_usuario_activo DEFAULT 1,
    intentos_fallidos  SMALLINT      NOT NULL CONSTRAINT DF_usuario_intentos DEFAULT 0
        CONSTRAINT CK_usuario_intentos CHECK (intentos_fallidos >= 0),
    ultimo_acceso      DATETIME2     NULL
);

-- Tabla 3.57 · BITACORA_AUDITORIA (RNF-03)
CREATE TABLE dbo.bitacora_auditoria (
    id_bitacora      INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_bitacora_auditoria PRIMARY KEY,
    id_usuario       INT           NOT NULL CONSTRAINT FK_bitacora_usuario REFERENCES dbo.usuario (id_usuario),
    accion           NVARCHAR(20)  NOT NULL
        CONSTRAINT CK_bitacora_accion CHECK (accion IN (N'Alta', N'Modificación', N'Cancelación', N'Baja lógica', N'Exportación')),
    entidad          NVARCHAR(40)  NOT NULL,
    id_registro      INT           NOT NULL,
    fecha_hora       DATETIME2     NOT NULL CONSTRAINT DF_bitacora_fecha_hora DEFAULT SYSUTCDATETIME(),
    valores_previos  NVARCHAR(MAX) NULL
);
CREATE INDEX IX_bitacora_fecha_hora ON dbo.bitacora_auditoria (fecha_hora);

-- Tabla 3.39 · SERVICIO (RF-04)
CREATE TABLE dbo.servicio (
    id_servicio       INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_servicio PRIMARY KEY,
    nombre            NVARCHAR(60)  NOT NULL,
    categoria         NVARCHAR(20)  NOT NULL
        CONSTRAINT CK_servicio_categoria CHECK (categoria IN (N'Consulta', N'Vacunación', N'Desparasitación',
                                                              N'Procedimiento menor', N'Estética', N'Aplicación')),
    precio            DECIMAL(10,2) NOT NULL CONSTRAINT CK_servicio_precio CHECK (precio >= 0),
    duracion_min      SMALLINT      NOT NULL CONSTRAINT CK_servicio_duracion CHECK (duracion_min > 0),
    puesto_requerido  NVARCHAR(15)  NOT NULL
        CONSTRAINT CK_servicio_puesto_requerido CHECK (puesto_requerido IN (N'Veterinario', N'Estilista')),
    agendable         BIT           NOT NULL CONSTRAINT DF_servicio_agendable DEFAULT 1,
    activo            BIT           NOT NULL CONSTRAINT DF_servicio_activo DEFAULT 1,
    -- RD-04: la estética la prestan estilistas; lo demás, veterinarios
    CONSTRAINT CK_servicio_compatibilidad_puesto CHECK (
        (categoria = N'Estética' AND puesto_requerido = N'Estilista')
        OR (categoria <> N'Estética' AND puesto_requerido = N'Veterinario'))
);

-- Tabla 3.40 · CITA (RF-05)
CREATE TABLE dbo.cita (
    id_cita             INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_cita PRIMARY KEY,
    id_mascota          INT           NOT NULL CONSTRAINT FK_cita_mascota REFERENCES dbo.mascota (id_mascota),
    id_empleado         INT           NOT NULL CONSTRAINT FK_cita_empleado REFERENCES dbo.empleado (id_empleado),
    id_servicio         INT           NOT NULL CONSTRAINT FK_cita_servicio REFERENCES dbo.servicio (id_servicio),
    fecha_hora_inicio   DATETIME2     NOT NULL,
    fecha_hora_fin      DATETIME2     NOT NULL,
    estado              NVARCHAR(12)  NOT NULL CONSTRAINT DF_cita_estado DEFAULT N'Programada'
        CONSTRAINT CK_cita_estado CHECK (estado IN (N'Programada', N'Completada', N'Cancelada')),
    motivo              NVARCHAR(200) NULL,
    motivo_cancelacion  NVARCHAR(150) NULL,
    CONSTRAINT CK_cita_fin_mayor_inicio CHECK (fecha_hora_fin > fecha_hora_inicio),
    -- RF-05: el motivo es obligatorio al cancelar
    CONSTRAINT CK_cita_cancelada_con_motivo
        CHECK (estado <> N'Cancelada' OR (motivo_cancelacion IS NOT NULL AND motivo_cancelacion <> N''))
);
-- RNF-05 y RD-02: agenda por empleado y fecha; incluye lo necesario para detectar empalmes
CREATE INDEX IX_cita_empleado_inicio ON dbo.cita (id_empleado, fecha_hora_inicio) INCLUDE (fecha_hora_fin, estado);
CREATE INDEX IX_cita_mascota ON dbo.cita (id_mascota);

/* ---------------------------------------------------------------------------
   Bloque C (primera parte) · Proveedores, productos y lotes
   (se crean antes del bloque clínico porque las aplicaciones descuentan lotes)
   --------------------------------------------------------------------------- */

-- Tabla 3.51 · PROVEEDOR (RF-12)
CREATE TABLE dbo.proveedor (
    id_proveedor      INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_proveedor PRIMARY KEY,
    razon_social      NVARCHAR(120) NOT NULL,
    rfc               NVARCHAR(13)  NULL,
    contacto          NVARCHAR(80)  NULL,
    telefono          NVARCHAR(15)  NOT NULL,
    correo            NVARCHAR(100) NULL,
    condiciones_pago  NVARCHAR(100) NULL,
    activo            BIT           NOT NULL CONSTRAINT DF_proveedor_activo DEFAULT 1
);
CREATE UNIQUE INDEX UX_proveedor_rfc ON dbo.proveedor (rfc) WHERE rfc IS NOT NULL;   -- D-12

-- Tabla 3.48 · PRODUCTO (RF-11)
CREATE TABLE dbo.producto (
    id_producto      INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_producto PRIMARY KEY,
    id_proveedor     INT           NULL CONSTRAINT FK_producto_proveedor REFERENCES dbo.proveedor (id_proveedor),
    codigo           NVARCHAR(20)  NOT NULL CONSTRAINT UQ_producto_codigo UNIQUE,
    nombre           NVARCHAR(100) NOT NULL,
    categoria        NVARCHAR(20)  NOT NULL
        CONSTRAINT CK_producto_categoria CHECK (categoria IN (N'Medicamento', N'Vacuna', N'Desparasitante',
                                                              N'Alimento', N'Accesorio', N'Insumo')),
    unidad_medida    NVARCHAR(15)  NOT NULL,
    precio_venta     DECIMAL(10,2) NOT NULL CONSTRAINT CK_producto_precio CHECK (precio_venta >= 0),
    stock_minimo     INT           NOT NULL CONSTRAINT DF_producto_stock_minimo DEFAULT 0
        CONSTRAINT CK_producto_stock_minimo CHECK (stock_minimo >= 0),
    requiere_receta  BIT           NOT NULL CONSTRAINT DF_producto_requiere_receta DEFAULT 0,   -- RD-12
    activo           BIT           NOT NULL CONSTRAINT DF_producto_activo DEFAULT 1
);

-- Tabla 3.49 · LOTE (RD-03, RD-05)
CREATE TABLE dbo.lote (
    id_lote              INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_lote PRIMARY KEY,
    id_producto          INT          NOT NULL CONSTRAINT FK_lote_producto REFERENCES dbo.producto (id_producto),
    numero_lote          NVARCHAR(30) NOT NULL,
    fecha_caducidad      DATE         NULL,   -- nula en productos sin caducidad
    cantidad_disponible  INT          NOT NULL CONSTRAINT DF_lote_cantidad DEFAULT 0
        CONSTRAINT CK_lote_cantidad_no_negativa CHECK (cantidad_disponible >= 0),   -- RD-05
    fecha_entrada        DATE         NOT NULL CONSTRAINT DF_lote_fecha_entrada DEFAULT CAST(GETDATE() AS DATE)
);
-- RD-05 y RNF-05: elegir el lote vigente que caduca primero
CREATE INDEX IX_lote_producto_caducidad ON dbo.lote (id_producto, fecha_caducidad) INCLUDE (cantidad_disponible);

-- Tabla 3.50 · MOVIMIENTO_INVENTARIO (RD-07: inmodificable, ver disparador al final)
CREATE TABLE dbo.movimiento_inventario (
    id_movimiento  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_movimiento_inventario PRIMARY KEY,
    id_lote        INT           NOT NULL CONSTRAINT FK_movimiento_lote REFERENCES dbo.lote (id_lote),
    id_empleado    INT           NOT NULL CONSTRAINT FK_movimiento_empleado REFERENCES dbo.empleado (id_empleado),
    tipo           NVARCHAR(15)  NOT NULL
        CONSTRAINT CK_movimiento_tipo CHECK (tipo IN (N'Entrada', N'Venta', N'Aplicación', N'Devolución', N'Ajuste')),
    cantidad       INT           NOT NULL,
    fecha_hora     DATETIME2     NOT NULL CONSTRAINT DF_movimiento_fecha_hora DEFAULT SYSUTCDATETIME(),
    referencia     NVARCHAR(40)  NULL,
    motivo         NVARCHAR(150) NULL,
    -- Con signo: positiva entra, negativa sale (Tabla 3.50)
    CONSTRAINT CK_movimiento_signo_cantidad CHECK (
        (tipo IN (N'Entrada', N'Devolución') AND cantidad > 0)
        OR (tipo IN (N'Venta', N'Aplicación') AND cantidad < 0)
        OR (tipo = N'Ajuste' AND cantidad <> 0)),
    -- El motivo es obligatorio en los ajustes (R08)
    CONSTRAINT CK_movimiento_ajuste_con_motivo CHECK (tipo <> N'Ajuste' OR (motivo IS NOT NULL AND motivo <> N''))
);
CREATE INDEX IX_movimiento_lote ON dbo.movimiento_inventario (id_lote, fecha_hora);

/* ---------------------------------------------------------------------------
   Bloque B · Expediente clínico y estética
   --------------------------------------------------------------------------- */

-- Tabla 3.41 · EXPEDIENTE_CLINICO (RF-06, RD-10)
CREATE TABLE dbo.expediente_clinico (
    id_expediente   INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_expediente_clinico PRIMARY KEY,
    id_mascota      INT           NOT NULL CONSTRAINT FK_expediente_mascota REFERENCES dbo.mascota (id_mascota)
                                           CONSTRAINT UQ_expediente_mascota UNIQUE,   -- RD-10: un solo expediente
    fecha_apertura  DATE          NOT NULL CONSTRAINT DF_expediente_fecha_apertura DEFAULT CAST(GETDATE() AS DATE),
    antecedentes    NVARCHAR(MAX) NULL,
    alergias        NVARCHAR(MAX) NULL    -- se muestran como alerta al abrir la consulta (RF-06)
);

-- Tabla 3.42 · CONSULTA (RF-06)
CREATE TABLE dbo.consulta (
    id_consulta     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_consulta PRIMARY KEY,
    id_expediente   INT           NOT NULL CONSTRAINT FK_consulta_expediente REFERENCES dbo.expediente_clinico (id_expediente),
    id_cita         INT           NOT NULL CONSTRAINT FK_consulta_cita REFERENCES dbo.cita (id_cita)
                                           CONSTRAINT UQ_consulta_cita UNIQUE,
    id_empleado     INT           NOT NULL CONSTRAINT FK_consulta_empleado REFERENCES dbo.empleado (id_empleado),
    fecha_hora      DATETIME2     NOT NULL CONSTRAINT DF_consulta_fecha_hora DEFAULT SYSUTCDATETIME(),
    sintomas        NVARCHAR(MAX) NOT NULL,
    peso_kg         DECIMAL(5,2)  NOT NULL CONSTRAINT CK_consulta_peso CHECK (peso_kg > 0),
    temperatura_c   DECIMAL(4,1)  NULL,
    diagnostico     NVARCHAR(MAX) NULL,
    tratamiento     NVARCHAR(MAX) NULL,
    observaciones   NVARCHAR(MAX) NULL,
    estado          NVARCHAR(10)  NOT NULL CONSTRAINT DF_consulta_estado DEFAULT N'Abierta'
        CONSTRAINT CK_consulta_estado CHECK (estado IN (N'Abierta', N'Firmada')),
    fecha_firma     DATETIME2     NULL,
    -- RF-06: la consulta firmada guarda la fecha de la firma
    CONSTRAINT CK_consulta_firmada_con_fecha CHECK (estado <> N'Firmada' OR fecha_firma IS NOT NULL)
);
CREATE INDEX IX_consulta_expediente ON dbo.consulta (id_expediente, fecha_hora);

-- Tabla 3.43 · APLICACION (RF-08)
CREATE TABLE dbo.aplicacion (
    id_aplicacion     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_aplicacion PRIMARY KEY,
    id_consulta       INT          NOT NULL CONSTRAINT FK_aplicacion_consulta REFERENCES dbo.consulta (id_consulta),
    id_lote           INT          NOT NULL CONSTRAINT FK_aplicacion_lote REFERENCES dbo.lote (id_lote),
    tipo              NVARCHAR(15) NOT NULL
        CONSTRAINT CK_aplicacion_tipo CHECK (tipo IN (N'Vacuna', N'Desparasitante', N'Otro')),
    cantidad          DECIMAL(8,2) NOT NULL CONSTRAINT CK_aplicacion_cantidad CHECK (cantidad > 0),
    dosis             NVARCHAR(30) NOT NULL,
    fecha_aplicacion  DATE         NOT NULL CONSTRAINT DF_aplicacion_fecha DEFAULT CAST(GETDATE() AS DATE),
    proxima_fecha     DATE         NULL,
    -- RF-08: en vacunas y desparasitantes la próxima fecha es obligatoria
    CONSTRAINT CK_aplicacion_proxima_fecha CHECK (tipo = N'Otro' OR proxima_fecha IS NOT NULL),
    -- R13: la próxima dosis no puede quedar antes o el mismo día de la aplicación
    CONSTRAINT CK_aplicacion_proxima_posterior CHECK (proxima_fecha IS NULL OR proxima_fecha > fecha_aplicacion)
);
CREATE INDEX IX_aplicacion_consulta ON dbo.aplicacion (id_consulta);
CREATE INDEX IX_aplicacion_proxima_fecha ON dbo.aplicacion (proxima_fecha) WHERE proxima_fecha IS NOT NULL;   -- RF-09

-- Tabla 3.44 · RECETA (RF-07)
CREATE TABLE dbo.receta (
    id_receta               INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_receta PRIMARY KEY,
    id_consulta             INT           NOT NULL CONSTRAINT FK_receta_consulta REFERENCES dbo.consulta (id_consulta),   -- RD-08
    folio                   NVARCHAR(20)  NOT NULL CONSTRAINT UQ_receta_folio UNIQUE,
    fecha_emision           DATETIME2     NOT NULL CONSTRAINT DF_receta_fecha_emision DEFAULT SYSUTCDATETIME(),
    indicaciones_generales  NVARCHAR(300) NULL
);

-- Tabla 3.45 · DETALLE_RECETA (llave sustituta + UK de la llave del diccionario, D-01)
CREATE TABLE dbo.detalle_receta (
    id_detalle_receta  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_detalle_receta PRIMARY KEY,
    id_receta          INT           NOT NULL CONSTRAINT FK_detalle_receta_receta REFERENCES dbo.receta (id_receta) ON DELETE CASCADE,
    id_producto        INT           NOT NULL CONSTRAINT FK_detalle_receta_producto REFERENCES dbo.producto (id_producto),
    dosis              NVARCHAR(50)  NOT NULL,
    frecuencia         NVARCHAR(50)  NOT NULL,
    duracion_dias      SMALLINT      NOT NULL CONSTRAINT CK_detalle_receta_duracion CHECK (duracion_dias > 0),
    indicaciones       NVARCHAR(200) NULL,
    CONSTRAINT UQ_detalle_receta_receta_producto UNIQUE (id_receta, id_producto)
);

-- Tabla 3.46 · REGISTRO_ESTETICA (RF-10)
CREATE TABLE dbo.registro_estetica (
    id_registro         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_registro_estetica PRIMARY KEY,
    id_cita             INT           NOT NULL CONSTRAINT FK_registro_estetica_cita REFERENCES dbo.cita (id_cita)
                                               CONSTRAINT UQ_registro_estetica_cita UNIQUE,
    estado_pelaje_piel  NVARCHAR(200) NOT NULL,
    hallazgos           NVARCHAR(300) NULL,
    aviso_veterinario   BIT           NOT NULL CONSTRAINT DF_registro_estetica_aviso DEFAULT 0,
    observaciones       NVARCHAR(300) NULL,
    fecha_hora          DATETIME2     NOT NULL CONSTRAINT DF_registro_estetica_fecha_hora DEFAULT SYSUTCDATETIME()
);

-- Tabla 3.47 · RECORDATORIO (RF-09)
CREATE TABLE dbo.recordatorio (
    id_recordatorio  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_recordatorio PRIMARY KEY,
    id_cliente       INT          NOT NULL CONSTRAINT FK_recordatorio_cliente REFERENCES dbo.cliente (id_cliente),
    id_aplicacion    INT          NULL CONSTRAINT FK_recordatorio_aplicacion REFERENCES dbo.aplicacion (id_aplicacion),
    id_cita          INT          NULL CONSTRAINT FK_recordatorio_cita REFERENCES dbo.cita (id_cita),
    tipo             NVARCHAR(15) NOT NULL
        CONSTRAINT CK_recordatorio_tipo CHECK (tipo IN (N'Próxima dosis', N'Cita')),
    fecha_objetivo   DATE         NOT NULL,
    estado           NVARCHAR(15) NOT NULL CONSTRAINT DF_recordatorio_estado DEFAULT N'Pendiente'
        CONSTRAINT CK_recordatorio_estado CHECK (estado IN (N'Pendiente', N'Contactado', N'Sin respuesta')),
    id_empleado      INT          NULL CONSTRAINT FK_recordatorio_empleado REFERENCES dbo.empleado (id_empleado),
    fecha_contacto   DATETIME2    NULL,
    -- Exactamente uno de aplicación o cita, y coherente con el tipo (apartado 3.4)
    CONSTRAINT CK_recordatorio_origen_unico CHECK (
        (tipo = N'Próxima dosis' AND id_aplicacion IS NOT NULL AND id_cita IS NULL)
        OR (tipo = N'Cita' AND id_cita IS NOT NULL AND id_aplicacion IS NULL)),
    -- RF-09: al marcarlo «Contactado» se registra quién y cuándo
    CONSTRAINT CK_recordatorio_contacto_registrado
        CHECK (estado <> N'Contactado' OR (id_empleado IS NOT NULL AND fecha_contacto IS NOT NULL))
);
CREATE INDEX IX_recordatorio_estado_fecha ON dbo.recordatorio (estado, fecha_objetivo);   -- lista diaria (RF-09)

/* ---------------------------------------------------------------------------
   Bloque C (segunda parte) · Compras y ventas
   --------------------------------------------------------------------------- */

-- Tabla 3.52 · PEDIDO_COMPRA (RF-12)
CREATE TABLE dbo.pedido_compra (
    id_pedido        INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_pedido_compra PRIMARY KEY,
    id_proveedor     INT           NOT NULL CONSTRAINT FK_pedido_proveedor REFERENCES dbo.proveedor (id_proveedor),
    id_empleado      INT           NOT NULL CONSTRAINT FK_pedido_empleado REFERENCES dbo.empleado (id_empleado),
    fecha_pedido     DATE          NOT NULL CONSTRAINT DF_pedido_fecha DEFAULT CAST(GETDATE() AS DATE),
    fecha_recepcion  DATE          NULL,
    estado           NVARCHAR(10)  NOT NULL CONSTRAINT DF_pedido_estado DEFAULT N'Pendiente'
        CONSTRAINT CK_pedido_estado CHECK (estado IN (N'Pendiente', N'Recibido', N'Cancelado')),
    total            DECIMAL(12,2) NOT NULL CONSTRAINT DF_pedido_total DEFAULT 0
        CONSTRAINT CK_pedido_total CHECK (total >= 0),
    CONSTRAINT CK_pedido_recibido_con_fecha CHECK (estado <> N'Recibido' OR fecha_recepcion IS NOT NULL)
);

-- Tabla 3.53 · DETALLE_PEDIDO (llave sustituta + UK de la llave del diccionario, D-01)
CREATE TABLE dbo.detalle_pedido (
    id_detalle_pedido    INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_detalle_pedido PRIMARY KEY,
    id_pedido            INT           NOT NULL CONSTRAINT FK_detalle_pedido_pedido REFERENCES dbo.pedido_compra (id_pedido) ON DELETE CASCADE,
    id_producto          INT           NOT NULL CONSTRAINT FK_detalle_pedido_producto REFERENCES dbo.producto (id_producto),
    cantidad_solicitada  INT           NOT NULL CONSTRAINT CK_detalle_pedido_solicitada CHECK (cantidad_solicitada > 0),
    cantidad_recibida    INT           NULL
        CONSTRAINT CK_detalle_pedido_recibida CHECK (cantidad_recibida IS NULL OR cantidad_recibida >= 0),
    costo_unitario       DECIMAL(10,2) NOT NULL CONSTRAINT CK_detalle_pedido_costo CHECK (costo_unitario >= 0),
    CONSTRAINT UQ_detalle_pedido_pedido_producto UNIQUE (id_pedido, id_producto)
);

-- Tabla 3.54 · VENTA (RF-13, RF-14)
CREATE TABLE dbo.venta (
    id_venta            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_venta PRIMARY KEY,
    folio_ticket        NVARCHAR(20)  NOT NULL CONSTRAINT UQ_venta_folio_ticket UNIQUE,
    id_cliente          INT           NOT NULL CONSTRAINT FK_venta_cliente REFERENCES dbo.cliente (id_cliente),
    id_empleado         INT           NOT NULL CONSTRAINT FK_venta_empleado REFERENCES dbo.empleado (id_empleado),
    id_cita             INT           NULL CONSTRAINT FK_venta_cita REFERENCES dbo.cita (id_cita),
    fecha_hora          DATETIME2     NOT NULL CONSTRAINT DF_venta_fecha_hora DEFAULT SYSUTCDATETIME(),
    total               DECIMAL(12,2) NOT NULL CONSTRAINT DF_venta_total DEFAULT 0
        CONSTRAINT CK_venta_total CHECK (total >= 0),
    saldo               DECIMAL(12,2) NOT NULL CONSTRAINT DF_venta_saldo DEFAULT 0,
    estado              NVARCHAR(10)  NOT NULL CONSTRAINT DF_venta_estado DEFAULT N'Pendiente'
        CONSTRAINT CK_venta_estado CHECK (estado IN (N'Pendiente', N'Pagada', N'Cancelada')),
    requiere_factura    BIT           NOT NULL CONSTRAINT DF_venta_requiere_factura DEFAULT 0,
    motivo_cancelacion  NVARCHAR(150) NULL,
    id_cancelo          INT           NULL CONSTRAINT FK_venta_cancelo REFERENCES dbo.empleado (id_empleado),
    -- RD-06: el saldo nunca es negativo ni mayor que el total
    CONSTRAINT CK_venta_saldo CHECK (saldo >= 0 AND saldo <= total),
    -- RF-13: el ticket pasa a «Pagada» solo con saldo cero
    CONSTRAINT CK_venta_pagada_saldo_cero CHECK (estado <> N'Pagada' OR saldo = 0),
    -- RF-14: la cancelación registra motivo y quién canceló
    CONSTRAINT CK_venta_cancelada_con_motivo CHECK (estado <> N'Cancelada'
        OR (motivo_cancelacion IS NOT NULL AND motivo_cancelacion <> N'' AND id_cancelo IS NOT NULL))
);
CREATE INDEX IX_venta_fecha_hora ON dbo.venta (fecha_hora);   -- corte de caja diario
CREATE INDEX IX_venta_cliente ON dbo.venta (id_cliente);

-- Tabla 3.55 · DETALLE_VENTA (llave sustituta + UK de la llave del diccionario, D-01)
CREATE TABLE dbo.detalle_venta (
    id_detalle_venta  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_detalle_venta PRIMARY KEY,
    id_venta          INT           NOT NULL CONSTRAINT FK_detalle_venta_venta REFERENCES dbo.venta (id_venta) ON DELETE CASCADE,
    numero_linea      SMALLINT      NOT NULL CONSTRAINT CK_detalle_venta_linea CHECK (numero_linea > 0),
    id_producto       INT           NULL CONSTRAINT FK_detalle_venta_producto REFERENCES dbo.producto (id_producto),
    id_servicio       INT           NULL CONSTRAINT FK_detalle_venta_servicio REFERENCES dbo.servicio (id_servicio),
    id_receta         INT           NULL CONSTRAINT FK_detalle_venta_receta REFERENCES dbo.receta (id_receta),
    cantidad          DECIMAL(8,2)  NOT NULL CONSTRAINT CK_detalle_venta_cantidad CHECK (cantidad > 0),
    precio_unitario   DECIMAL(10,2) NOT NULL CONSTRAINT CK_detalle_venta_precio CHECK (precio_unitario >= 0),   -- RD-11
    subtotal          DECIMAL(12,2) NOT NULL CONSTRAINT CK_detalle_venta_subtotal CHECK (subtotal >= 0),
    CONSTRAINT UQ_detalle_venta_venta_linea UNIQUE (id_venta, numero_linea),
    -- Exactamente uno de producto o servicio (apartado 3.4)
    CONSTRAINT CK_detalle_venta_producto_o_servicio CHECK (
        (id_producto IS NOT NULL AND id_servicio IS NULL) OR (id_producto IS NULL AND id_servicio IS NOT NULL)),
    -- RD-12: el folio de receta solo acompaña a un producto
    CONSTRAINT CK_detalle_venta_receta_producto CHECK (id_receta IS NULL OR id_producto IS NOT NULL)
);

-- Tabla 3.56 · PAGO (RF-13, RF-14)
CREATE TABLE dbo.pago (
    id_pago         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_pago PRIMARY KEY,
    id_venta        INT           NOT NULL CONSTRAINT FK_pago_venta REFERENCES dbo.venta (id_venta),
    id_empleado     INT           NOT NULL CONSTRAINT FK_pago_empleado REFERENCES dbo.empleado (id_empleado),
    tipo            NVARCHAR(10)  NOT NULL CONSTRAINT CK_pago_tipo CHECK (tipo IN (N'Abono', N'Devolución')),
    metodo          NVARCHAR(15)  NOT NULL
        CONSTRAINT CK_pago_metodo CHECK (metodo IN (N'Efectivo', N'Tarjeta', N'Transferencia')),
    monto           DECIMAL(12,2) NOT NULL CONSTRAINT CK_pago_monto CHECK (monto > 0),
    monto_recibido  DECIMAL(12,2) NULL,
    cambio          DECIMAL(12,2) NULL,
    fecha_hora      DATETIME2     NOT NULL CONSTRAINT DF_pago_fecha_hora DEFAULT SYSUTCDATETIME(),
    referencia      NVARCHAR(40)  NULL,
    -- RD-06: cambio = monto_recibido − monto, y nunca negativo. El tope del abono (no mayor al saldo)
    -- se valida en la transacción de cobro con la venta bloqueada, porque un CHECK no consulta otra tabla.
    CONSTRAINT CK_pago_cambio CHECK (
        (monto_recibido IS NULL AND cambio IS NULL)
        OR (monto_recibido IS NOT NULL AND monto_recibido >= monto AND cambio = monto_recibido - monto))
);
CREATE INDEX IX_pago_venta ON dbo.pago (id_venta);
CREATE INDEX IX_pago_fecha_hora ON dbo.pago (fecha_hora) INCLUDE (tipo, metodo, monto);   -- corte de caja

COMMIT TRANSACTION;
GO

/* ---------------------------------------------------------------------------
   RD-07 · Los movimientos de inventario no se modifican ni se borran:
   los errores se corrigen con un nuevo movimiento de tipo «Ajuste».
   --------------------------------------------------------------------------- */
CREATE OR ALTER TRIGGER dbo.TR_movimiento_inventario_inmutable
ON dbo.movimiento_inventario
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    -- Dentro de un disparador XACT_ABORT está activo por defecto y THROW anularía toda la transacción
    -- de la aplicación. Con XACT_ABORT OFF y RAISERROR solo se rechaza esta instrucción: la aplicación
    -- recibe el error y decide (Django revierte hasta su punto de guardado).
    SET XACT_ABORT OFF;
    RAISERROR (N'RD-07: los movimientos de inventario no se modifican ni se borran; registre un ajuste con motivo.', 16, 1);
    RETURN;
END;
GO

PRINT N'26 tablas de Dogtor creadas. Siguiente paso: bd\02_vistas.sql';
GO
