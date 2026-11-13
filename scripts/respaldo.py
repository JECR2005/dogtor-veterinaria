#!/usr/bin/env python3
"""S0-21 · Respaldo y restauración de la base de datos (RNF-04, riesgo crítico R05).

RNF-04: respaldo diario completo fuera del horario de atención, copia externa al servidor, conservación
de 30 días y restauración en menos de 2 horas, probada una vez por prototipo (Tabla 4.28).

Subcomandos:
    python scripts/respaldo.py respaldar
        Crea respaldos/dogtor_AAAA-MM-DD_HHMM.dump (pg_dump, formato personalizado), lo copia a
        RESPALDO_COPIA_EXTERNA si está definida y borra los respaldos con más de RESPALDO_DIAS_RETENCION días.

    python scripts/respaldo.py restaurar ARCHIVO --base NOMBRE
        Crea la base NOMBRE y restaura en ella el archivo indicado (servidor limpio, apartado 4.6.1).

    python scripts/respaldo.py probar [ARCHIVO]
        Prueba de restauración (TS-07): restaura el respaldo indicado (o el más reciente) en una base
        temporal, mide el tiempo, cuenta las tablas, borra la base temporal y anota el resultado en
        docs/gestion/registro_restauraciones.md.

Configuración: variables DB_* y RESPALDO_* del archivo .env (ver .env.example).
Requiere las utilidades de PostgreSQL (pg_dump, pg_restore, createdb, dropdb, psql) en el PATH.
En el servidor se programa con cron a las 22:00 h:
    0 22 * * * cd /srv/dogtor && .venv/bin/python scripts/respaldo.py respaldar \
        >> /var/log/dogtor_respaldo.log 2>&1
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / "docs" / "gestion" / "registro_restauraciones.md"
META_MINUTOS = 120
BASE_TEMPORAL = "dogtor_prueba_restauracion"


def cargar_env():
    """Lee .env sin depender de paquetes externos; las variables ya definidas tienen prioridad."""
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ.setdefault(clave.strip(), valor.strip())


def conexion():
    return {
        "base": os.environ.get("DB_NOMBRE", "dogtor"),
        "usuario": os.environ.get("DB_USUARIO", "dogtor_app"),
        "host": os.environ.get("DB_HOST", "localhost"),
        "puerto": os.environ.get("DB_PUERTO", "5432"),
    }


def ejecutar(comando, base=None):
    """Ejecuta una utilidad de PostgreSQL con la contraseña en PGPASSWORD (nunca en la línea de comandos)."""
    c = conexion()
    entorno = dict(os.environ, PGPASSWORD=os.environ.get("DB_CONTRASENA", ""))
    completo = [comando[0], "-h", c["host"], "-p", c["puerto"], "-U", c["usuario"], *comando[1:]]
    if base:
        completo += ["-d", base]
    resultado = subprocess.run(completo, env=entorno, capture_output=True, text=True)
    if resultado.returncode != 0:
        sys.exit(f"Error en {comando[0]}: {resultado.stderr.strip()}")
    return resultado.stdout


def directorio_respaldos():
    ruta = Path(os.environ.get("RESPALDO_DIR", "./respaldos"))
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def depurar(directorio, dias):
    limite = datetime.now() - timedelta(days=dias)
    borrados = 0
    for archivo in directorio.glob("dogtor_*.dump"):
        if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            borrados += 1
    return borrados


def respaldar(_args):
    c = conexion()
    destino = directorio_respaldos() / f"dogtor_{datetime.now():%Y-%m-%d_%H%M}.dump"
    inicio = time.monotonic()
    ejecutar(["pg_dump", "-Fc", "--no-owner", "-f", str(destino)], base=c["base"])
    print(
        f"Respaldo creado: {destino} ({destino.stat().st_size / 1024:.1f} KB, "
        f"{time.monotonic() - inicio:.1f} s)"
    )

    dias = int(os.environ.get("RESPALDO_DIAS_RETENCION", "30"))
    externa = os.environ.get("RESPALDO_COPIA_EXTERNA", "").strip()
    if externa:
        externa = Path(externa)
        externa.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destino, externa / destino.name)
        print(f"Copia externa: {externa / destino.name}")
        depurar(externa, dias)
    else:
        print("Aviso: RESPALDO_COPIA_EXTERNA no está definida; RNF-04 exige una copia fuera del servidor.")
    borrados = depurar(directorio_respaldos(), dias)
    print(f"Retención de {dias} días: {borrados} respaldo(s) antiguo(s) eliminado(s).")


def restaurar_en(archivo, base):
    c = conexion()
    entorno = dict(os.environ, PGPASSWORD=os.environ.get("DB_CONTRASENA", ""))
    creacion = subprocess.run(
        ["createdb", "-h", c["host"], "-p", c["puerto"], "-U", c["usuario"], base],
        env=entorno,
        capture_output=True,
        text=True,
    )
    if creacion.returncode != 0:
        sys.exit(f"Error en createdb: {creacion.stderr.strip()}")
    ejecutar(["pg_restore", "--no-owner", "--exit-on-error", str(archivo)], base=base)


def restaurar(args):
    archivo = Path(args.archivo)
    if not archivo.exists():
        sys.exit(f"No existe el archivo {archivo}")
    inicio = time.monotonic()
    restaurar_en(archivo, args.base)
    print(
        f"Restaurado {archivo.name} en la base «{args.base}» en {(time.monotonic() - inicio) / 60:.2f} min."
    )


def borrar_base(base):
    c = conexion()
    entorno = dict(os.environ, PGPASSWORD=os.environ.get("DB_CONTRASENA", ""))
    subprocess.run(
        ["dropdb", "--if-exists", "-h", c["host"], "-p", c["puerto"], "-U", c["usuario"], base],
        env=entorno,
        capture_output=True,
        text=True,
    )


def probar(args):
    if args.archivo:
        archivo = Path(args.archivo)
    else:
        respaldos = sorted(directorio_respaldos().glob("dogtor_*.dump"))
        if not respaldos:
            sys.exit("No hay respaldos. Ejecuta primero: python scripts/respaldo.py respaldar")
        archivo = respaldos[-1]

    borrar_base(BASE_TEMPORAL)
    inicio = time.monotonic()
    restaurar_en(archivo, BASE_TEMPORAL)
    minutos = (time.monotonic() - inicio) / 60
    tablas = int(
        ejecutar(
            [
                "psql",
                "-tA",
                "-c",
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'",
            ],
            base=BASE_TEMPORAL,
        ).strip()
    )
    borrar_base(BASE_TEMPORAL)

    cumple = minutos < META_MINUTOS
    resultado = "Cumple" if cumple else "NO CUMPLE"
    print(
        f"Prueba de restauración: {archivo.name} · {minutos:.2f} min ({minutos * 60:.1f} s) · "
        f"{tablas} tablas · "
        f"{resultado} (meta < {META_MINUTOS} min)"
    )

    if not REGISTRO.exists():
        REGISTRO.write_text(
            "# Registro de pruebas de restauración (RNF-04, TS-07)\n\n"
            "Meta: restaurar un respaldo en menos de 120 minutos, una vez por prototipo.\n\n"
            "| Fecha | Prototipo | Respaldo | Tiempo (min) | Tablas restauradas | Resultado | Ejecutó |\n"
            "|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(
            f"| {datetime.now():%Y-%m-%d %H:%M} | {args.prototipo} | {archivo.name} | {minutos:.2f} | "
            f"{tablas} | {resultado} | {args.ejecuto} |\n"
        )
    print(f"Anotado en {REGISTRO.relative_to(RAIZ)}")
    if not cumple:
        sys.exit(1)


def main():
    cargar_env()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="accion", required=True)
    sub.add_parser("respaldar", help="crea un respaldo completo").set_defaults(func=respaldar)
    r = sub.add_parser("restaurar", help="restaura un respaldo en una base nueva")
    r.add_argument("archivo")
    r.add_argument("--base", required=True, help="nombre de la base nueva")
    r.set_defaults(func=restaurar)
    t = sub.add_parser("probar", help="prueba de restauración cronometrada (TS-07)")
    t.add_argument("archivo", nargs="?")
    t.add_argument("--prototipo", default="S0", help="prototipo en curso (S0, P1 … P5)")
    t.add_argument(
        "--ejecuto",
        default=os.environ.get("USER") or os.environ.get("USERNAME") or "",
        help="quién la ejecuta",
    )
    t.set_defaults(func=probar)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
