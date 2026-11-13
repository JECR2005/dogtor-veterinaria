"""Servicios (reglas de negocio) del componente «Seguridad y acceso».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P1 y P5:

- RNF-01: inicio de sesión, bloqueo al quinto intento fallido y permisos por rol (P1).
- RNF-03: registro en bitácora de cambios en ventas, consultas, recetas, inventario y bajas (P1/P5).
- RNF-08: exportación de contactos solo para el Administrador, con registro en bitácora (P5).
"""
