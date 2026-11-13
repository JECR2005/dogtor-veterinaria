/* =============================================================================
   Dogtor · 99 · Borra la vista, el disparador y las 26 tablas  ·  SOLO DESARROLLO
   Sirve para recrear el esquema desde cero en una computadora local (después: 01 y 02).
   NUNCA ejecutar en producción: se pierden todos los datos. Antes, haga un respaldo.
   ============================================================================= */

IF DB_NAME() NOT IN (N'Dogtor', N'test_Dogtor')
    THROW 50099, N'Este script solo se ejecuta en las bases Dogtor (local) o test_Dogtor.', 1;
-- (sin GO aquí: si la validación falla, THROW detiene todo el lote y no se borra nada)

DROP VIEW IF EXISTS dbo.vista_stock_disponible;
DROP TRIGGER IF EXISTS dbo.TR_movimiento_inventario_inmutable;

-- Orden inverso al de creación, para respetar las llaves foráneas
DROP TABLE IF EXISTS dbo.pago;
DROP TABLE IF EXISTS dbo.detalle_venta;
DROP TABLE IF EXISTS dbo.venta;
DROP TABLE IF EXISTS dbo.detalle_pedido;
DROP TABLE IF EXISTS dbo.pedido_compra;
DROP TABLE IF EXISTS dbo.recordatorio;
DROP TABLE IF EXISTS dbo.registro_estetica;
DROP TABLE IF EXISTS dbo.detalle_receta;
DROP TABLE IF EXISTS dbo.receta;
DROP TABLE IF EXISTS dbo.aplicacion;
DROP TABLE IF EXISTS dbo.consulta;
DROP TABLE IF EXISTS dbo.expediente_clinico;
DROP TABLE IF EXISTS dbo.movimiento_inventario;
DROP TABLE IF EXISTS dbo.lote;
DROP TABLE IF EXISTS dbo.producto;
DROP TABLE IF EXISTS dbo.proveedor;
DROP TABLE IF EXISTS dbo.cita;
DROP TABLE IF EXISTS dbo.servicio;
DROP TABLE IF EXISTS dbo.bitacora_auditoria;
DROP TABLE IF EXISTS dbo.usuario;
DROP TABLE IF EXISTS dbo.horario_laboral;
DROP TABLE IF EXISTS dbo.empleado;
DROP TABLE IF EXISTS dbo.mascota;
DROP TABLE IF EXISTS dbo.cliente;
DROP TABLE IF EXISTS dbo.raza;
DROP TABLE IF EXISTS dbo.especie;
GO

PRINT N'Esquema de Dogtor borrado.';
GO
