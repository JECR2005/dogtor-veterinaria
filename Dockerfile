# S5-12 · Imagen del servidor de Dogtor para el entorno con https (Tabla 4.2, D-22, D-25).
#   target «web»:   Gunicorn + Django (config.settings.produccion) con el ODBC Driver 18 de Microsoft.
#   target «nginx»: Nginx con TLS y los archivos estáticos ya recolectados.
# Se construye y levanta con docker-compose.yml (scripts/preparar_produccion.ps1).

# --- Aplicación -------------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS web

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.produccion

# ODBC Driver 18 for SQL Server (D-09); se aceptan los términos de Microsoft con ACCEPT_EULA
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg ca-certificates \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
       | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
       -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
    && apt-get purge -y gnupg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-prod.txt ./
RUN pip install -r requirements-prod.txt

COPY . .
# Los estáticos se recolectan al construir; las variables solo existen durante este paso
RUN DJANGO_SECRET_KEY=solo-para-construir DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput \
    && useradd --create-home --uid 10001 dogtor \
    && chown -R dogtor /app
USER dogtor

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:8000/salud/', headers={'Host': 'dogtor.local', 'X-Forwarded-Proto': 'https'}), timeout=4)"
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", \
     "--access-logfile", "-", "--forwarded-allow-ips", "*"]

# --- Proxy con TLS ----------------------------------------------------------------------------------
FROM nginx:1.27-alpine AS nginx
COPY docker/nginx/dogtor.conf /etc/nginx/conf.d/default.conf
COPY --from=web /app/staticfiles /srv/static
