"""Pruebas automatizadas con pytest y en la integración continua (apartado 4.5.1)."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "solo-para-pruebas-automatizadas")

from .base import *  # noqa: E402,F403

DEBUG = False

# Hash rápido solo para que las pruebas no tarden; producción usa el hash con sal por defecto (RNF-01).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LOGGING = {"version": 1, "disable_existing_loggers": False}
DOGTOR_ADMIN_HABILITADO = False
DOGTOR_PERMITIR_DATOS_PRUEBA = True
