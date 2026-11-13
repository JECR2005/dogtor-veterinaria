"""Configuración común a todos los entornos del sistema Dogtor."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # python-dotenv es opcional en producción (variables del servicio)
    pass


def env(nombre, defecto=None, obligatorio=False):
    """Lee una variable de entorno. Las claves nunca se escriben en el código (Tabla 4.26)."""
    valor = os.environ.get(nombre, defecto)
    if obligatorio and not valor:
        raise ImproperlyConfigured(f"Falta la variable de entorno {nombre} (ver .env.example)")
    return valor


SECRET_KEY = env("DJANGO_SECRET_KEY", obligatorio=True)
DEBUG = False
ALLOWED_HOSTS = [
    h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

# --- Aplicaciones -------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Una app por componente de la Tabla 3.2 (Tabla 4.24)
DOGTOR_APPS = [
    "seguridad",
    "catalogos",
    "agenda",
    "clinico",
    "inventario",
    "ventas",
    "recordatorios",
    "reportes",
]

INSTALLED_APPS = DJANGO_APPS + DOGTOR_APPS

# S0-13 · Usuario propio con los campos de la Tabla 3.38. Debe definirse antes de la primera migración.
AUTH_USER_MODEL = "seguridad.Usuario"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "seguridad.context_processors.menu",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Base de datos (PostgreSQL, Tabla 4.2) ------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NOMBRE", "dogtor"),
        "USER": env("DB_USUARIO", "dogtor_app"),
        "PASSWORD": env("DB_CONTRASENA", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PUERTO", "5432"),
        "ATOMIC_REQUESTS": False,  # las transacciones con bloqueo se abren en los servicios (RD-05, RD-06)
        "CONN_MAX_AGE": 60,
    }
}

# El diccionario de datos usa INT para las llaves (apartado 3.5)
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# --- Contraseñas (RNF-01): hash con sal mediante los mecanismos de Django -------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Comando cargar_datos_prueba: solo en local, pruebas automatizadas y entorno de pruebas (cláusula Undécima)
DOGTOR_PERMITIR_DATOS_PRUEBA = False

# Bloqueo de cuenta al quinto intento fallido (RNF-01); la lógica se programa en P1.
DOGTOR_INTENTOS_MAXIMOS = 5

# Se definen en P1 junto con las pantallas de acceso (UI-01)
LOGIN_URL = "/cuenta/entrar/"
LOGIN_REDIRECT_URL = "/"

# --- Idioma y zona horaria ---------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Monterrey"  # Tampico, Tamaulipas (tiempo del centro, sin horario de verano)
USE_I18N = True
USE_TZ = True
# RI-13: fechas día/mes/año, hora de 24 horas e importes con separador de miles ($1,250.00)
USE_THOUSAND_SEPARATOR = True

# Horario de atención (RNF-06): lunes a sábado de 9:00 a 19:00 h
DOGTOR_HORARIO_ATENCION = {"dias": range(1, 7), "apertura": "09:00", "cierre": "19:00"}

# --- Archivos estáticos -------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Sesión ---------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 10  # una jornada de atención
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": "INFO"},
}
