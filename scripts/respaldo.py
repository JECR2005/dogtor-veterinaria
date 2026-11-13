#!/usr/bin/env python3
"""S0-21 · Respaldo y restauración de la base de datos en SQL Server (RNF-04, riesgo crítico R05).

RNF-04: respaldo diario completo fuera del horario de atención, copia externa al servidor, conservación
de 30 días y restauración en menos de 2 horas, probada una vez por prototipo (Tabla 4.28).

Subcomandos:
    python scripts/respaldo.py respaldar
        BACKUP DATABASE a RESPALDO_DIR\\Dogtor_AAAA-MM-DD_HHMM.bak (con CHECKSUM), copia a
        RESPALDO_COPIA_EXTERNA si está definida y borra los .bak con más de RESPALDO_DIAS_RETENCION días.

    python scripts/respaldo.py restaurar ARCHIVO --base NOMBRE
        RESTORE en una base nueva NOMBRE, moviendo los archivos a las carpetas por defecto de la instancia.

    python scripts/respaldo.py probar [ARCHIVO] --prototipo P1
        Prueba de restauración (TS-07): restaura el .bak indicado (o el más reciente) en una base temporal,
        mide el tiempo, cuenta las tablas, borra la base temporal y anota el resultado en
        docs/gestion/registro_restauraciones.md.

Configuración: variables DB_* y RESPALDO_* del archivo .env (ver .env.example).
- RESPALDO_DIR es una carpeta del equipo donde corre SQL Server y la cuenta del servicio debe poder escribir
  en ella. Este script lee esa misma carpeta para copiar y depurar, así que debe ejecutarse en ese equipo.
- La cuenta necesita permiso de respaldo (db_owner) y, para restaurar, crear bases (dbcreator o sysadmin).
- SQL Server Express no tiene el Agente SQL: el respaldo diario se programa con el Programador de tareas
  de Windows (README, sección Respaldo). Express tampoco comprime respaldos; por eso no se usa COMPRESSION.
"""

import argparse
import os
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path, PureWindowsPath

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / "docs" / "gestion" / "registro_restauraciones.md"
META_MINUTOS = 120
BASE_TEMPORAL = "Dogtor_prueba_restauracion"


def cargar_env():
    """Lee .env sin depender de paquetes externos; las variables ya definidas tienen prioridad."""
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ.setdefault(clave.strip(), valor.strip())


def conectar():
    """Conexión a master en modo autocommit (BACKUP y RESTORE no se permiten dentro de una transacción)."""
    try:
        import pyodbc
    except ImportError:
        sys.exit("Falta pyodbc. Activa el entorno virtual e instala requirements.txt.")
    servidor = os.environ.get("DB_HOST", r"localhost\SQLEXPRESS")
    if os.environ.get("DB_PUERTO"):
        servidor = f"{servidor},{os.environ['DB_PUERTO']}"
    partes = [
        f"DRIVER={{{os.environ.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server')}}}",
        f"SERVER={servidor}",
        "DATABASE=master",
    ]
    usuario = os.environ.get("DB_USUARIO", "")
    if usuario:
        partes += [f"UID={usuario}", f"PWD={os.environ.get('DB_CONTRASENA', '')}"]
    else:
        partes.append("Trusted_Connection=yes")
    if os.environ.get("DB_CONFIAR_CERTIFICADO", "si").lower() in ("si", "sí", "true", "1"):
        partes.append("TrustServerCertificate=yes")
    return pyodbc.connect(";".join(partes), autocommit=True)


def ejecutar(conexion, sql, *parametros):
    """Ejecuta y espera a que SQL Server termine (BACKUP y RESTORE envían varios mensajes de avance)."""
    cursor = conexion.cursor()
    cursor.execute(sql, *parametros)
    filas = cursor.fetchall() if cursor.description else []
    while cursor.nextset():
        pass
    return filas


def nombre_base():
    return os.environ.get("DB_NOMBRE", "Dogtor")


def directorio_respaldos():
    ruta = os.environ.get("RESPALDO_DIR", "").strip()
    if not ruta:
        sys.exit("Define RESPALDO_DIR en .env con una ruta absoluta (por ejemplo C:\\DogtorRespaldos).")
    Path(ruta).mkdir(parents=True, exist_ok=True)
    return Path(ruta)


def corchetes(nombre):
    """Nombre de base entre corchetes para T-SQL (no admite parámetros en BACKUP/RESTORE/CREATE)."""
    return "[" + nombre.replace("]", "]]") + "]"


def depurar(directorio, dias):
    limite = datetime.now() - timedelta(days=dias)
    borrados = 0
    for archivo in Path(directorio).glob(f"{nombre_base()}_*.bak"):
        if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            borrados += 1
    return borrados


def respaldar(_args):
    base = nombre_base()
    destino = directorio_respaldos() / f"{base}_{datetime.now():%Y-%m-%d_%H%M}.bak"
    inicio = time.monotonic()
    with conectar() as conexion:
        ejecutar(
            conexion,
            f"BACKUP DATABASE {corchetes(base)} TO DISK = ? WITH INIT, CHECKSUM, NAME = ?",
            str(destino),
            f"Respaldo completo de {base} (RNF-04)",
        )
        ejecutar(conexion, "RESTORE VERIFYONLY FROM DISK = ? WITH CHECKSUM", str(destino))
    print(
        f"Respaldo verificado: {destino} ({destino.stat().st_size / 1_048_576:.1f} MB, "
        f"{time.monotonic() - inicio:.1f} s)"
    )

    dias = int(os.environ.get("RESPALDO_DIAS_RETENCION", "30"))
    externa = os.environ.get("RESPALDO_COPIA_EXTERNA", "").strip()
    if externa:
        Path(externa).mkdir(parents=True, exist_ok=True)
        shutil.copy2(destino, Path(externa) / destino.name)
        print(f"Copia externa: {Path(externa) / destino.name}")
        depurar(externa, dias)
    else:
        print("Aviso: RESPALDO_COPIA_EXTERNA no está definida; RNF-04 exige una copia fuera del servidor.")
    print(
        f"Retención de {dias} días: {depurar(directorio_respaldos(), dias)} "
        "respaldo(s) antiguo(s) eliminado(s)."
    )


def restaurar_en(conexion, archivo, base):
    """RESTORE con MOVE de cada archivo lógico a las carpetas por defecto de la instancia."""
    archivos = ejecutar(conexion, "RESTORE FILELISTONLY FROM DISK = ?", str(archivo))
    rutas = ejecutar(
        conexion,
        "SELECT CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS NVARCHAR(400)), "
        "CAST(SERVERPROPERTY('InstanceDefaultLogPath') AS NVARCHAR(400))",
    )[0]
    datos, bitacora = rutas[0], rutas[1]
    separador = "\\" if "\\" in (datos or "") else "/"
    movimientos, parametros = [], []
    for fila in archivos:
        logico, tipo = fila.LogicalName, fila.Type  # D = datos, L = registro de transacciones
        carpeta = bitacora if tipo == "L" else datos
        extension = ".ldf" if tipo == "L" else ".mdf"
        fisico = f"{carpeta.rstrip(separador)}{separador}{base}_{logico}{extension}"
        movimientos.append("MOVE ? TO ?")
        parametros += [logico, fisico]
    ejecutar(
        conexion,
        f"RESTORE DATABASE {corchetes(base)} FROM DISK = ? "
        f"WITH {', '.join(movimientos)}, RECOVERY, STATS = 25",
        str(archivo),
        *parametros,
    )


def borrar_base(conexion, base):
    if ejecutar(conexion, "SELECT DB_ID(?)", base)[0][0] is not None:
        ejecutar(conexion, f"ALTER DATABASE {corchetes(base)} SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        ejecutar(conexion, f"DROP DATABASE {corchetes(base)}")


def restaurar(args):
    if args.base.lower() == nombre_base().lower():
        sys.exit("Por seguridad, restaura en una base con otro nombre y luego cambia DB_NOMBRE en .env.")
    inicio = time.monotonic()
    with conectar() as conexion:
        if ejecutar(conexion, "SELECT DB_ID(?)", args.base)[0][0] is not None:
            sys.exit(f"La base «{args.base}» ya existe.")
        restaurar_en(conexion, args.archivo, args.base)
    print(
        f"Restaurado {PureWindowsPath(args.archivo).name} en «{args.base}» en "
        f"{(time.monotonic() - inicio) / 60:.2f} min."
    )


def probar(args):
    if args.archivo:
        archivo = args.archivo
    else:
        respaldos = sorted(directorio_respaldos().glob(f"{nombre_base()}_*.bak"))
        if not respaldos:
            sys.exit("No hay respaldos. Ejecuta primero: python scripts/respaldo.py respaldar")
        archivo = str(respaldos[-1])

    with conectar() as conexion:
        borrar_base(conexion, BASE_TEMPORAL)
        inicio = time.monotonic()
        restaurar_en(conexion, archivo, BASE_TEMPORAL)
        minutos = (time.monotonic() - inicio) / 60
        tablas = ejecutar(
            conexion,
            f"SELECT COUNT(*) FROM {corchetes(BASE_TEMPORAL)}.INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE'",
        )[0][0]
        borrar_base(conexion, BASE_TEMPORAL)

    cumple = minutos < META_MINUTOS
    resultado = "Cumple" if cumple else "NO CUMPLE"
    nombre = PureWindowsPath(archivo).name
    print(
        f"Prueba de restauración: {nombre} · {minutos:.2f} min ({minutos * 60:.1f} s) · "
        f"{tablas} tablas · {resultado} (meta < {META_MINUTOS} min)"
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
            f"| {datetime.now():%Y-%m-%d %H:%M} | {args.prototipo} | {nombre} | {minutos:.2f} | "
            f"{tablas} | {resultado} | {args.ejecuto} |\n"
        )
    print(f"Anotado en {REGISTRO.relative_to(RAIZ)}")
    if not cumple:
        sys.exit(1)


def main():
    cargar_env()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="accion", required=True)
    sub.add_parser("respaldar", help="crea y verifica un respaldo completo").set_defaults(func=respaldar)
    r = sub.add_parser("restaurar", help="restaura un respaldo en una base nueva")
    r.add_argument("archivo", help="ruta del .bak en el equipo del servidor")
    r.add_argument("--base", required=True, help="nombre de la base nueva")
    r.set_defaults(func=restaurar)
    t = sub.add_parser("probar", help="prueba de restauración cronometrada (TS-07)")
    t.add_argument("archivo", nargs="?")
    t.add_argument("--prototipo", default="S0", help="prototipo en curso (S0, P1 … P5)")
    t.add_argument(
        "--ejecuto",
        default=os.environ.get("USERNAME") or os.environ.get("USER") or "",
        help="quién la ejecuta",
    )
    t.set_defaults(func=probar)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
