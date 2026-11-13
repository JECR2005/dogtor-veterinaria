"""Servicios (reglas de negocio) del componente «Inventario y compras».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P2:

- RF-11, RD-03 y RD-05: lotes por caducidad, stock disponible calculado y alertas (P2).
- RF-12: pedidos de compra; al recibirlos se crean los lotes (P2).
- RD-07: movimientos inmodificables; correcciones mediante ajuste con motivo (P2).
"""
