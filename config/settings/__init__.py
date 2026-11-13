"""Configuración por entorno (S0-11, Tabla 4.3).

- local.py       Cada integrante, con datos ficticios. DEBUG activo y admin de Django disponible.
- test.py        Pruebas automatizadas (pytest y CI). Hash de contraseña rápido.
- pruebas.py     Entorno de pruebas: copia del prototipo para la evaluación del personal.
- produccion.py  Servidor del local: TLS obligatorio, sin DEBUG, sin admin de Django.
"""
