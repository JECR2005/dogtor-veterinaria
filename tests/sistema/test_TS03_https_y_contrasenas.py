"""TS-03 · Cifrado en tránsito y contraseñas (Tabla 4.15, RNF-01, D-25).

Criterio: todo viaja por https y las contraseñas se guardan con hash y sal. En la laptop se comprueba además
abriendo https://dogtor.local (guion del bloque D); aquí se revisa lo que lo garantiza:

- `check --deploy` con la configuración de producción no da ningún aviso.
- La configuración de producción redirige a https, marca las cookies como seguras y envía HSTS.
- Nginx solo atiende https (TLS 1.2 o 1.3) y agrega las cabeceras de seguridad a todo.
- Las contraseñas se guardan con PBKDF2 y una sal distinta cada vez; D-15 terminó (el entorno local ya exige
  las reglas de RNF-01).
- Los secretos y el certificado no entran al repositorio ni a la imagen.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth.hashers import check_password, identify_hasher, make_password

from seguridad.models import Rol

pytestmark = pytest.mark.sistema

RAIZ = Path(__file__).resolve().parents[2]


def _django(*argumentos, settings="config.settings.produccion"):
    entorno = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": settings,
        "DJANGO_SECRET_KEY": "x" * 30 + "clave-larga-de-prueba-para-check-deploy-1234567890",
        "DJANGO_ALLOWED_HOSTS": "dogtor.local",
    }
    return subprocess.run(
        [sys.executable, *argumentos], cwd=RAIZ, env=entorno, capture_output=True, text=True, timeout=120
    )


def test_TS03_check_deploy_sin_avisos():
    resultado = _django("manage.py", "check", "--deploy", "--fail-level", "WARNING")
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "no issues" in resultado.stdout


def test_TS03_produccion_solo_https_con_cookies_seguras():
    codigo = (
        "from django.conf import settings as s; import django; django.setup();"
        "print(s.DEBUG, s.SECURE_SSL_REDIRECT, s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, "
        "s.SECURE_HSTS_SECONDS >= 2592000, s.SECURE_PROXY_SSL_HEADER, s.CSRF_TRUSTED_ORIGINS)"
    )
    resultado = _django("-c", codigo)
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == (
        "False True True True True ('HTTP_X_FORWARDED_PROTO', 'https') ['https://dogtor.local']"
    )


def test_TS03_d15_termino_el_entorno_local_exige_las_reglas_de_contrasena():
    codigo = (
        "from django.conf import settings as s; import django; django.setup();"
        "print(len(s.AUTH_PASSWORD_VALIDATORS))"
    )
    resultado = _django("-c", codigo, settings="config.settings.local")
    assert resultado.returncode == 0, resultado.stderr
    assert int(resultado.stdout.strip()) == 4


def test_TS03_nginx_solo_https_y_con_cabeceras_de_seguridad():
    conf = (RAIZ / "docker" / "nginx" / "dogtor.conf").read_text(encoding="utf-8")
    assert "return 301 https://$host$request_uri;" in conf
    assert "ssl_protocols       TLSv1.2 TLSv1.3;" in conf and "server_tokens off;" in conf
    for cabecera in (
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "X-Frame-Options",
        "Permissions-Policy",
        "Content-Security-Policy",
    ):
        assert f'add_header {cabecera} "' in conf and conf.count(cabecera) >= 2, cabecera
    assert "frame-ancestors 'none'" in conf and "object-src 'none'" in conf
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")
    assert '"443:443"' in compose and "8000:" not in compose  # Gunicorn no se publica fuera de Docker


@pytest.mark.parametrize("archivo", [".gitignore", ".dockerignore"])
def test_TS03_secretos_y_certificado_fuera_del_repositorio_y_de_la_imagen(archivo):
    reglas = (RAIZ / archivo).read_text(encoding="utf-8").splitlines()
    for regla in (".env", "docker/produccion.env", "docker/certs/"):
        assert regla in reglas, f"{archivo} no excluye {regla}"


def test_TS03_contrasenas_con_hash_y_sal():
    primero, segundo = make_password("Clave-Prueba-2026"), make_password("Clave-Prueba-2026")
    assert primero != segundo  # misma contraseña, distinta sal
    algoritmo, iteraciones, sal, _ = primero.split("$")
    assert algoritmo == "pbkdf2_sha256" and int(iteraciones) >= 600_000 and len(sal) >= 16
    assert identify_hasher(primero).algorithm == "pbkdf2_sha256"
    assert check_password("Clave-Prueba-2026", primero) and not check_password("clave-prueba-2026", primero)


@pytest.mark.django_db
def test_TS03_en_la_base_la_contrasena_nunca_esta_en_texto_plano(crear_usuario):
    from django.db import connection

    cuenta = crear_usuario("admin", contrasena="Clave-Prueba-2026", rol=Rol.ADMINISTRADOR)
    with connection.cursor() as cursor:
        cursor.execute("SELECT hash_contrasena FROM dbo.usuario WHERE id_usuario = %s", [cuenta.pk])
        guardada = cursor.fetchone()[0]
    assert "Clave-Prueba-2026" not in guardada and guardada.startswith("pbkdf2_sha256$")
