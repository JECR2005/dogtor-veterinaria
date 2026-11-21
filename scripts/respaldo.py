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
        Prueba de restauración por prototipo: restaura el .bak indicado (o el más reciente) en una base
        temporal del mismo servidor, mide el tiempo, cuenta las tablas, borra la base temporal y anota el
        resultado en docs/gestion/registro_restauraciones.md.

    python scripts/respaldo.py ts07 [--conservar]
        TS-07 (S5-09, D-24): respalda la base ahora, la restaura en un SERVIDOR LIMPIO (el contenedor de
        docker/servidor_limpio.yml), revisa su integridad (DBCC CHECKDB) y compara el número de registros de
        cada tabla con la base original. Deja el detalle en docs/gestion/ts07_restauracion.md y una línea en
        el registro de restauraciones. Ejecútelo sin nadie usando el sistema, para que los conteos no cambien.

Configuración: variables DB_*, RESPALDO_* y RESTAURACION_* del archivo .env (ver .env.example).
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
DETALLE_TS07 = RAIZ / "docs" / "gestion" / "ts07_restauracion.md"
META_MINUTOS = 120
BASE_TEMPORAL = "Dogtor_prueba_restauracion"
BASE_TS07 = "Dogtor_TS07"
ENCABEZADO_REGISTRO = (
    "# Registro de pruebas de restauración (RNF-04, TS-07)\n\n"
    "Meta: restaurar un respaldo en menos de 120 minutos, una vez por prototipo.\n\n"
    "| Fecha | Prototipo | Respaldo | Tamaño | Respaldo (s) | Restauración (s) | Tablas restauradas "
    "| Resultado | Ejecutó |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
)


def cargar_env():
    """Lee .env sin depender de paquetes externos; las variables ya definidas tienen prioridad."""
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ.setdefault(clave.strip(), valor.strip())


def conectar(servidor=None, usuario=None, contrasena=None):
    """Conexión a master en modo autocommit (BACKUP y RESTORE no se permiten dentro de una transacción).

    Sin argumentos usa el servidor de .env (DB_*); para TS-07 recibe los datos del servidor limpio.
    """
    try:
        import pyodbc
    except ImportError:
        sys.exit("Falta pyodbc. Activa el entorno virtual e instala requirements.txt.")
    if servidor is None:
        servidor = os.environ.get("DB_HOST", r"localhost\SQLEXPRESS")
        if os.environ.get("DB_PUERTO"):
            servidor = f"{servidor},{os.environ['DB_PUERTO']}"
        usuario = os.environ.get("DB_USUARIO", "")
        contrasena = os.environ.get("DB_CONTRASENA", "")
    partes = [
        f"DRIVER={{{os.environ.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server')}}}",
        f"SERVER={servidor}",
        "DATABASE=master",
    ]
    if usuario:
        partes += [f"UID={usuario}", f"PWD={contrasena or ''}"]
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
    """Respaldo verificado con copia externa y retención. Devuelve (archivo, segundos que tardó)."""
    base = nombre_base()
    destino = directorio_respaldos() / f"{base}_{datetime.now():%Y-%m-%d_%H%M%S}.bak"
    inicio = time.monotonic()
    with conectar() as conexion:
        ejecutar(
            conexion,
            f"BACKUP DATABASE {corchetes(base)} TO DISK = ? WITH INIT, CHECKSUM, NAME = ?",
            str(destino),
            f"Respaldo completo de {base} (RNF-04)",
        )
        ejecutar(conexion, "RESTORE VERIFYONLY FROM DISK = ? WITH CHECKSUM", str(destino))
    segundos = time.monotonic() - inicio
    print(f"Respaldo verificado: {destino} ({destino.stat().st_size / 1_048_576:.1f} MB, {segundos:.1f} s)")

    dias = int(os.environ.get("RESPALDO_DIAS_RETENCION", "30"))
    # Acepta variables de Windows, por ejemplo %USERPROFILE%\OneDrive\DogtorRespaldos
    externa = os.path.expandvars(os.environ.get("RESPALDO_COPIA_EXTERNA", "").strip())
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
    return destino, segundos


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

    anotar(
        args.prototipo,
        f"`{nombre}`",
        _tamano(archivo),
        "—",
        minutos * 60,
        f"{tablas}",
        resultado,
        args.ejecuto,
    )
    if not cumple:
        sys.exit(1)


def _tamano(archivo):
    try:
        return f"{Path(archivo).stat().st_size / 1_048_576:.2f} MB"
    except OSError:
        return "—"


def anotar(prototipo, respaldo, tamano, seg_respaldo, seg_restauracion, tablas, resultado, ejecuto):
    """Agrega una línea al registro de restauraciones (Tabla 4.28)."""
    if not REGISTRO.exists():
        REGISTRO.write_text(ENCABEZADO_REGISTRO, encoding="utf-8")
    seg_respaldo = seg_respaldo if isinstance(seg_respaldo, str) else f"{seg_respaldo:.2f}"
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(
            f"| {datetime.now():%Y-%m-%d %H:%M} | {prototipo} | {respaldo} | {tamano} | {seg_respaldo} | "
            f"{seg_restauracion:.2f} | {tablas} | {resultado} | {ejecuto} |\n"
        )
    print(f"Anotado en {REGISTRO.relative_to(RAIZ)}")


# --- S5-09 · TS-07: restauración en un servidor limpio con conteo de registros -----------------------
def conteos(conexion, base):
    """Número exacto de registros de cada tabla de la base: {"esquema.tabla": n}."""
    tablas = ejecutar(
        conexion,
        f"SELECT s.name, t.name FROM {corchetes(base)}.sys.tables AS t "
        f"JOIN {corchetes(base)}.sys.schemas AS s ON s.schema_id = t.schema_id "
        "WHERE t.is_ms_shipped = 0 ORDER BY s.name, t.name",
    )
    return {
        f"{esquema}.{tabla}": ejecutar(
            conexion, f"SELECT COUNT_BIG(*) FROM {corchetes(base)}.{corchetes(esquema)}.{corchetes(tabla)}"
        )[0][0]
        for esquema, tabla in tablas
    }


def comparar(origen, restaurada):
    """Filas (tabla, registros en el origen, restaurados, iguales) de las tablas de los dos lados."""
    return [
        (tabla, origen.get(tabla), restaurada.get(tabla), origen.get(tabla) == restaurada.get(tabla))
        for tabla in sorted(set(origen) | set(restaurada))
    ]


def detalle_ts07(datos):
    """Markdown con el resultado de TS-07 (docs/gestion/ts07_restauracion.md)."""
    filas = datos["filas"]
    diferentes = [f for f in filas if not f[3]]
    lineas = [
        "# TS-07 · Restauración en un servidor limpio (RNF-04)",
        "",
        "Generado por `python scripts/respaldo.py ts07` (S5-09, D-24). Criterio de la Tabla 4.15: "
        "restauración en menos de 120 minutos y datos íntegros.",
        "",
        "| Dato | Valor |",
        "|---|---|",
        f"| Fecha | {datos['fecha']:%Y-%m-%d %H:%M} |",
        f"| Base de origen | `{datos['base']}` en `{datos['servidor_origen']}` |",
        f"| Servidor limpio | `{datos['servidor_limpio']}` · {datos['version']} |",
        f"| Respaldo | `{datos['archivo']}` · {datos['tamano']} · {datos['seg_respaldo']:.2f} s |",
        f"| Restauración | {datos['seg_restauracion']:.2f} s ({datos['seg_restauracion'] / 60:.2f} min) |",
        "| Integridad (DBCC CHECKDB) | Sin errores |",
        f"| Tablas | {len(filas)} · {len(filas) - len(diferentes)} con el mismo número de registros |",
        f"| Registros | {sum(f[1] or 0 for f in filas):,} en el origen · {sum(f[2] or 0 for f in filas):,} "
        "restaurados |",
        f"| Resultado | **{datos['resultado']}** |",
        f"| Ejecutó | {datos['ejecuto']} |",
        "",
        "| Tabla | Origen | Restaurada | Igual |",
        "|---|---:|---:|:---:|",
    ]
    for tabla, a, b, igual in filas:
        origen, restaurada = "—" if a is None else a, "—" if b is None else b
        lineas.append(f"| `{tabla}` | {origen} | {restaurada} | {'Sí' if igual else '**No**'} |")
    return "\n".join(lineas) + "\n"


def ts07(args):
    servidor = os.environ.get("RESTAURACION_HOST", "localhost,14330")
    usuario = os.environ.get("RESTAURACION_USUARIO", "sa")
    contrasena = os.environ.get("RESTAURACION_CONTRASENA", "")
    carpeta = os.environ.get("RESTAURACION_CARPETA", "/respaldos").rstrip("/\\")
    if not contrasena:
        sys.exit("Define RESTAURACION_CONTRASENA en .env (la del usuario sa del servidor limpio, D-24).")

    print("1/4 Respaldo de la base en uso…")
    archivo, seg_respaldo = respaldar(args)
    with conectar() as origen_cx:
        origen = conteos(origen_cx, nombre_base())

    print(f"2/4 Restauración en el servidor limpio {servidor}…")
    with conectar(servidor, usuario, contrasena) as limpio:
        version = ejecutar(limpio, "SELECT CAST(SERVERPROPERTY('ProductVersion') AS NVARCHAR(40))")[0][0]
        edicion = ejecutar(limpio, "SELECT CAST(SERVERPROPERTY('Edition') AS NVARCHAR(80))")[0][0]
        borrar_base(limpio, BASE_TS07)
        inicio = time.monotonic()
        restaurar_en(limpio, f"{carpeta}/{archivo.name}", BASE_TS07)
        seg_restauracion = time.monotonic() - inicio
        print("3/4 Integridad (DBCC CHECKDB) y conteo de registros…")
        ejecutar(limpio, f"DBCC CHECKDB ({corchetes(BASE_TS07)}) WITH NO_INFOMSGS")  # si hay daño, falla aquí
        restaurada = conteos(limpio, BASE_TS07)
        if not args.conservar:
            borrar_base(limpio, BASE_TS07)

    filas = comparar(origen, restaurada)
    iguales = all(igual for *_, igual in filas)
    cumple = seg_restauracion / 60 < META_MINUTOS and iguales
    resultado = "Cumple" if cumple else "NO CUMPLE"
    datos = {
        "fecha": datetime.now(),
        "base": nombre_base(),
        "servidor_origen": os.environ.get("DB_HOST", ""),
        "servidor_limpio": servidor,
        "version": f"SQL Server {version} ({edicion})",
        "archivo": archivo.name,
        "tamano": _tamano(archivo),
        "seg_respaldo": seg_respaldo,
        "seg_restauracion": seg_restauracion,
        "filas": filas,
        "resultado": resultado,
        "ejecuto": args.ejecuto,
    }
    DETALLE_TS07.write_text(detalle_ts07(datos), encoding="utf-8")
    print(
        f"4/4 TS-07: {seg_restauracion:.2f} s · {sum(f[3] for f in filas)} de {len(filas)} tablas con los "
        f"mismos registros · {resultado}. Detalle en {DETALLE_TS07.relative_to(RAIZ)}"
    )
    anotar(
        args.prototipo,
        f"`{archivo.name}` en servidor limpio (TS-07, D-24), CHECKDB sin errores",
        datos["tamano"],
        seg_respaldo,
        seg_restauracion,
        f"{len(filas)}, conteos {'iguales' if iguales else 'DIFERENTES'}",
        resultado,
        args.ejecuto,
    )
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
    s = sub.add_parser("ts07", help="TS-07: restauración en un servidor limpio comparando registros")
    s.add_argument("--conservar", action="store_true", help="no borrar la base restaurada al terminar")
    s.add_argument("--prototipo", default="P5")
    s.add_argument("--ejecuto", default=os.environ.get("USERNAME") or os.environ.get("USER") or "")
    s.set_defaults(func=ts07)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
