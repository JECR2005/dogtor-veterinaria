"""Servicios (reglas de negocio) del componente «Expediente clínico».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P3:

- RF-06, RD-01 y RD-07: consulta con firma; solo lectura después de firmar (P3).
- RF-07 y RD-08: receta con folio dentro de una consulta abierta, sin descontar existencias (P3).
- RF-08 y RD-09: aplicación que descuenta una sola vez el lote que caduca primero (P3).
- RF-10: registro de estética y aviso al veterinario (P3).
"""
