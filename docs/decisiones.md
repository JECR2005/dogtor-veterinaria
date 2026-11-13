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
  necesitan `NULL` para admitir varios registros sin valor.
- **Actualizar documento:** No.

## D-03 · Restricciones CHECK adicionales

- **Decisión:** además de las listas de valores permitidos, la base valida reglas que el diccionario describe
  en texto: cédula obligatoria para Veterinario (RD-01), compatibilidad servicio–puesto (RD-04), motivo obligatorio
  al cancelar citas y ventas, fecha de firma en consultas firmadas, próxima fecha obligatoria en vacunas y
  desparasitantes y posterior a la aplicación (R13), signo de la cantidad según el tipo de movimiento, motivo en
  ajustes, saldo entre 0 y el total, ticket «Pagada» solo con saldo cero, cambio = recibido − monto, recordatorio
  con exactamente un origen coherente con su tipo, y aceptación obligatoria del aviso de privacidad (RNF-08).
- **Motivo:** la base protege las reglas aunque falle el código (apartado 4.6.1, "Restricciones en la base").
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

- **Decisión:** serie 5.2 LTS (soporte de seguridad hasta abril de 2028), que cubre el desarrollo y la garantía.
- **Actualizar documento:** Opcional. Apartado 4.1, Tabla 4.2.

## D-07 · Calendario con vistas estándar de FullCalendar

- **Decisión:** la vista por empleado de RF-05 se arma con las vistas estándar (licencia MIT) y un filtro por
  empleado, porque las vistas por recurso son de licencia comercial (ver `docs/componentes.md`).
- **Actualizar documento:** No.

## D-08 · Archivo de configuración de pruebas automatizadas

- **Decisión:** además de los entornos de la Tabla 4.3 (local, pruebas y producción) existe
  `config/settings/test.py` para pytest y la integración continua.
- **Actualizar documento:** No.
