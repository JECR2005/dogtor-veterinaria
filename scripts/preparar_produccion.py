#!/usr/bin/env python3
"""S5-12 · Cuenta de SQL Server y variables del entorno con https en Docker (D-25).

Lo llama scripts/preparar_produccion.ps1 después de habilitar TCP/IP y la autenticación de SQL Server:

    python scripts/preparar_produccion.py

1. Crea docker/produccion.env (si no existe) con una clave secreta y una contraseña nuevas, generadas aquí:
   nadie las escribe ni las ve, y el archivo nunca se sube al repositorio (.gitignore).
2. Crea o actualiza la cuenta dogtor_web en SQL Server con privilegio mínimo (RNF-01): solo lee y escribe
   datos de la base (db_datareader y db_datawriter); no crea tablas ni bases. Usa la conexión de .env (su
   cuenta de Windows) para hacerlo.
3. Comprueba que dogtor_web entra por TCP (localhost,1433), como lo hará el contenedor.
4. Apunta el monitor de TS-08 (MONITOR_URL de .env) a https://dogtor.local/salud/.
"""

import os
import re
import secrets
import string
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scripts import respaldo  # noqa: E402  (cargar_env, conectar, ejecutar, corchetes)

PRODUCCION = RAIZ / "docker" / "produccion.env"
CUENTA = "dogtor_web"
DOMINIO = "dogtor.local"
URL_SALUD = f"https://{DOMINIO}/salud/"


def contrasena_nueva(largo=24):
    """Cumple la política de SQL Server y no lleva caracteres que molesten en .env, ODBC o Docker."""
    alfabeto = string.ascii_letters + string.digits
    while True:
        valor = "".join(secrets.choice(alfabeto) for _ in range(largo - 2)) + "-9"
        if any(c.islower() for c in valor) and any(c.isupper() for c in valor):
            return valor


def leer_env(archivo):
    valores = {}
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip()
    return valores


def contenido_produccion(base, clave_secreta, contrasena):
    return "\n".join(
        [
            "# Generado por scripts/preparar_produccion.py (S5-12, D-25). NO se sube al repositorio.",
            "# Variables del contenedor «web» (docker-compose.yml).",
            f"DJANGO_SECRET_KEY={clave_secreta}",
            f"DJANGO_ALLOWED_HOSTS={DOMINIO},localhost,127.0.0.1",
            f"DB_NOMBRE={base}",
            "DB_HOST=host.docker.internal",
            "DB_PUERTO=1433",
            f"DB_USUARIO={CUENTA}",
            f"DB_CONTRASENA={contrasena}",
            "DB_DRIVER=ODBC Driver 18 for SQL Server",
            "DB_CONFIAR_CERTIFICADO=si",
            "",
        ]
    )


def preparar_archivo(base):
    """Crea docker/produccion.env una sola vez; si ya existe, conserva su clave y su contraseña."""
    actuales = leer_env(PRODUCCION)
    if actuales.get("DB_CONTRASENA") and actuales.get("DJANGO_SECRET_KEY"):
        return actuales["DB_CONTRASENA"], False
    contrasena = contrasena_nueva()
    PRODUCCION.parent.mkdir(parents=True, exist_ok=True)
    PRODUCCION.write_text(contenido_produccion(base, secrets.token_urlsafe(50), contrasena), encoding="utf-8")
    return contrasena, True


# La cuenta va fija (dogtor_web); la contraseña y la base llegan como parámetros y se citan con QUOTENAME
SQL_CUENTA = """
DECLARE @contrasena NVARCHAR(128) = ?, @base SYSNAME = ?, @sql NVARCHAR(MAX);
IF SUSER_ID(N'dogtor_web') IS NULL
    SET @sql = N'CREATE LOGIN dogtor_web WITH PASSWORD = ' + QUOTENAME(@contrasena, '''')
             + N', CHECK_POLICY = ON, DEFAULT_DATABASE = ' + QUOTENAME(@base);
ELSE
    SET @sql = N'ALTER LOGIN dogtor_web WITH PASSWORD = ' + QUOTENAME(@contrasena, '''')
             + N', CHECK_POLICY = ON; ALTER LOGIN dogtor_web ENABLE;';
EXEC (@sql);
SET @sql = N'USE ' + QUOTENAME(@base) + N';
IF USER_ID(N''dogtor_web'') IS NULL CREATE USER dogtor_web FOR LOGIN dogtor_web;
ALTER ROLE db_datareader ADD MEMBER dogtor_web;
ALTER ROLE db_datawriter ADD MEMBER dogtor_web;';
EXEC (@sql);
"""


def crear_cuenta(contrasena, base):
    with respaldo.conectar() as conexion:
        solo_windows = respaldo.ejecutar(
            conexion, "SELECT CAST(SERVERPROPERTY('IsIntegratedSecurityOnly') AS INT)"
        )[0][0]
        if solo_windows == 1:
            sys.exit(
                "SQL Server solo acepta cuentas de Windows. Ejecute scripts\\preparar_produccion.ps1 como "
                "administrador: habilita la autenticación de SQL Server y reinicia el servicio."
            )
        respaldo.ejecutar(conexion, SQL_CUENTA, contrasena, base)
    print(f"Cuenta {CUENTA}: lee y escribe datos de {base}; no crea tablas ni bases (RNF-01).")


def probar_tcp(contrasena, base):
    with respaldo.conectar("localhost,1433", CUENTA, contrasena) as conexion:
        cuentas = respaldo.ejecutar(conexion, f"SELECT COUNT(*) FROM {respaldo.corchetes(base)}.dbo.usuario")[
            0
        ][0]
    print(f"{CUENTA} entra por TCP (localhost,1433) y lee la base: {cuentas} cuentas del sistema.")


def apuntar_monitor(archivo=RAIZ / ".env", url=URL_SALUD):
    texto = archivo.read_text(encoding="utf-8") if archivo.exists() else ""
    if re.search(r"^MONITOR_URL=", texto, flags=re.MULTILINE):
        texto = re.sub(r"^MONITOR_URL=.*$", f"MONITOR_URL={url}", texto, flags=re.MULTILINE)
    else:
        texto = texto.rstrip("\n") + f"\nMONITOR_URL={url}\n"
    archivo.write_text(texto, encoding="utf-8")
    print(f"Monitor de TS-08 apuntando a {url}")


def main():
    respaldo.cargar_env()
    base = os.environ.get("DB_NOMBRE", "Dogtor")
    contrasena, nueva = preparar_archivo(base)
    estado = "creado con clave y contraseña nuevas" if nueva else "ya existía"
    print(f"{PRODUCCION.relative_to(RAIZ)}: {estado}.")
    crear_cuenta(contrasena, base)
    probar_tcp(contrasena, base)
    apuntar_monitor()


if __name__ == "__main__":
    main()
