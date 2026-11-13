"""Servicios (reglas de negocio) del componente «Ventas y caja».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P4:

- RF-13, RD-06 y RD-11: tickets, pagos parciales con cambio, precio histórico y corte de caja (P4).
- RD-12: producto con control solo con folio de receta válido (P4).
- RF-14: cancelación con permisos según haya pagos; reintegro de productos vendidos (P4).
"""
