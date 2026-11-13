#!/usr/bin/env python3
"""Ejecuta los scripts T-SQL de la carpeta bd/ sobre la base configurada en .env.

Es una alternativa a abrirlos en SSMS. Usa la misma conexión que Django (mssql-django), así que
basta con tener el .env listo. Las pruebas automatizadas usan este módulo para crear las tablas
en la base de pruebas (tests/conftest.py).

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python bd/ejecutar.py              # 01_tablas.sql y 02_vistas.sql
    python bd/ejecutar.py --recrear    # SOLO LOCAL: 99_borrar_tablas.sql y luego 01 y 02
"""

import argparse
import os
import re
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parent

SCRIPTS_ESQUEMA = [CARPETA / "01_tablas.sql", CARPETA / "02_vistas.sql"]
SCRIPT_BORRAR = CARPETA / "99_borrar_tablas.sql"

_SEPARADOR_GO = re.compile(r"^\s*GO\s*;?\s*$", re.IGNORECASE | re.MULTILINE)


def lotes_de_script(ruta):
    """Divide un script en lotes por las líneas «GO», como lo hacen SSMS y sqlcmd."""
    texto = Path(ruta).read_text(encoding="utf-8")
    return [lote.strip() for lote in _SEPARADOR_GO.split(texto) if lote.strip()]


def ejecutar_scripts(conexion, rutas):
    """Ejecuta cada lote de los scripts indicados con una conexión de Django."""
    with conexion.cursor() as cursor:
        for ruta in rutas:
            for lote in lotes_de_script(ruta):
                cursor.execute(lote)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--recrear", action="store_true", help="borra y vuelve a crear el esquema (solo local)")
    args = p.parse_args()

    sys.path.insert(0, str(RAIZ))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection

    rutas = list(SCRIPTS_ESQUEMA)
    if args.recrear:
        if not settings.DEBUG:
            sys.exit("--recrear solo se permite en el entorno local (DEBUG activo).")
        rutas.insert(0, SCRIPT_BORRAR)

    print(f"Base: {settings.DATABASES['default']['NAME']} en {settings.DATABASES['default']['HOST']}")
    ejecutar_scripts(connection, rutas)
    for ruta in rutas:
        print(f"  ✓ {ruta.name}")
    print("Esquema listo.")


if __name__ == "__main__":
    main()
