"""Punto de entrada WSGI para Gunicorn (Tabla 4.2)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.produccion")

application = get_wsgi_application()
