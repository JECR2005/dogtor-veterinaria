"""Producción: Nginx con TLS delante de Gunicorn, en Docker (Tablas 4.2 y 4.26, D-22, D-25).

`python manage.py check --deploy --settings=config.settings.produccion` no debe dar ningún aviso (TS-03); la
integración continua lo revisa con la imagen de Docker y `tests/unidad/test_TS03_produccion.py`.
"""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", obligatorio=True).split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]

# Cifrado en tránsito: solo https con redirección desde http (RNF-01, TS-03). Nginx termina el TLS y avisa
# a Django con X-Forwarded-Proto; Gunicorn solo escucha dentro de la red de Docker.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# Solo marca el encabezado: el dominio no se inscribe en la lista de precarga de los navegadores (D-25).
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Gunicorn: los archivos estáticos los sirve Nginx desde la imagen (collectstatic al construirla)
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

DOGTOR_ADMIN_HABILITADO = False
