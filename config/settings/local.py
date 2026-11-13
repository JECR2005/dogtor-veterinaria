"""Entorno local: cada integrante, con datos ficticios (Tabla 4.3)."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "solo-para-desarrollo-local-no-usar-en-produccion")

from .base import *  # noqa: E402,F403
from .base import INSTALLED_APPS  # noqa: E402

DEBUG = True

# El sitio de administración de Django solo existe en local; en producción se deshabilita (Tabla 4.26).
INSTALLED_APPS = ["django.contrib.admin", *INSTALLED_APPS]
DOGTOR_ADMIN_HABILITADO = True
DOGTOR_PERMITIR_DATOS_PRUEBA = True
