#!/usr/bin/env python3
"""S5-10 · Monitor de disponibilidad en el horario de atención (RNF-06, TS-08, D-22).

RNF-06: 99 % de disponibilidad de lunes a sábado de 9:00 a 19:00 h. El Programador de tareas ejecuta
`revisar` cada 5 minutos en ese horario (scripts/programar_tareas.ps1); cada revisión consulta /salud/
(que también prueba la base de datos) y deja una línea en logs/disponibilidad.csv.

Subcomandos:
    python scripts/monitor.py revisar [--forzar]
        Una revisión. Fuera del horario de atención no hace nada (salvo con --forzar, para probarlo).

    python scripts/monitor.py reporte [--desde AAAA-MM-DD] [--hasta AAAA-MM-DD]
        Resume las revisiones del periodo en docs/gestion/disponibilidad_TS08.md: horas laborales, horas
        monitoreadas, caídas (con su inicio y duración) y el porcentaje de caída sobre lo monitoreado.

Configuración en .env:
    MONITOR_URL            dirección de /salud/ (defecto http://127.0.0.1:8000/salud/)
    MONITOR_VERIFICAR_TLS  si | no (no, para el certificado local del entorno con https de D-22)
    MONITOR_INTERVALO_MIN  minutos entre revisiones (defecto 5)

Solo usa la biblioteca estándar: no depende de Django ni de la base, para poder reportar que se cayeron.
"""

import argparse
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "logs" / "disponibilidad.csv"
REPORTE = RAIZ / "docs" / "gestion" / "disponibilidad_TS08.md"
COLUMNAS = ["fecha_hora", "resultado", "codigo", "milisegundos", "detalle"]
ARRIBA, CAIDA = "Arriba", "Caída"
APERTURA, CIERRE = 9, 19  # RNF-06: de 9:00 a 19:00 h
DIAS_DE_SERVICIO = range(0, 6)  # lunes (0) a sábado (5)
META_CAIDA = 1.0  # % máximo de caída en horas laborales (Tabla 4.15)
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def cargar_env():
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ.setdefault(clave.strip(), valor.strip())


def en_horario(momento):
    """¿El momento cae en el horario de atención (lunes a sábado, de 9:00 a 19:00)?"""
    return momento.weekday() in DIAS_DE_SERVICIO and APERTURA <= momento.hour < CIERRE


def intervalo():
    return int(os.environ.get("MONITOR_INTERVALO_MIN", "5"))


# --- Revisar ------------------------------------------------------------------------------------
def consultar(url, verificar_tls=True, espera=10):
    """GET a /salud/. Devuelve (resultado, código HTTP, milisegundos, detalle)."""
    contexto = None
    if url.startswith("https") and not verificar_tls:
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=espera, context=contexto) as respuesta:  # noqa: S310
            cuerpo = respuesta.read(2000).decode("utf-8", "replace")
            codigo = respuesta.status
    except urllib.error.HTTPError as error:  # 503 si la base no responde
        return CAIDA, error.code, round((time.monotonic() - inicio) * 1000), f"HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        motivo = getattr(error, "reason", error)
        return CAIDA, 0, round((time.monotonic() - inicio) * 1000), f"Sin respuesta: {motivo}"[:200]
    milisegundos = round((time.monotonic() - inicio) * 1000)
    try:
        estado = json.loads(cuerpo).get("estado")
    except (ValueError, AttributeError):
        estado = None
    if codigo == 200 and estado == "ok":
        return ARRIBA, codigo, milisegundos, ""
    return CAIDA, codigo, milisegundos, f"Respuesta inesperada: {cuerpo[:100]}"


def anotar(fila, archivo=None):
    archivo = archivo or ARCHIVO
    archivo.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not archivo.exists()
    with archivo.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        if nuevo:
            escritor.writerow(COLUMNAS)
        escritor.writerow(fila)


def revisar(args):
    ahora = datetime.now()
    if not en_horario(ahora) and not args.forzar:
        print("Fuera del horario de atención: no se revisa (use --forzar para probar).")
        return 0
    url = os.environ.get("MONITOR_URL", "http://127.0.0.1:8000/salud/")
    verificar = os.environ.get("MONITOR_VERIFICAR_TLS", "si").lower() in ("si", "sí", "true", "1")
    resultado, codigo, milisegundos, detalle = consultar(url, verificar)
    anotar([ahora.isoformat(timespec="seconds"), resultado, codigo, milisegundos, detalle])
    print(f"{ahora:%Y-%m-%d %H:%M:%S} · {url} · {resultado} ({codigo}, {milisegundos} ms) {detalle}".rstrip())
    return 0 if resultado == ARRIBA else 1


# --- Reporte ------------------------------------------------------------------------------------
@dataclass
class Revision:
    momento: datetime
    arriba: bool
    milisegundos: int
    detalle: str


def leer(archivo=None):
    archivo = archivo or ARCHIVO
    if not archivo.exists():
        return []
    with archivo.open(newline="", encoding="utf-8") as f:
        return [
            Revision(
                datetime.fromisoformat(r["fecha_hora"]),
                r["resultado"] == ARRIBA,
                int(r["milisegundos"] or 0),
                r["detalle"],
            )
            for r in csv.DictReader(f)
        ]


def horas_laborales(desde, hasta):
    """Horas del horario de atención entre dos fechas, inclusive."""
    dias = (desde + timedelta(days=n) for n in range((hasta - desde).days + 1))
    return sum(CIERRE - APERTURA for dia in dias if dia.weekday() in DIAS_DE_SERVICIO)


def caidas(revisiones, minutos):
    """Agrupa revisiones caídas consecutivas en incidentes: [(inicio, revisiones, minutos estimados)]."""
    incidentes, actual = [], None
    for revision in sorted(revisiones, key=lambda r: r.momento):
        if revision.arriba:
            actual = None
            continue
        seguida = actual and revision.momento - actual[-1].momento <= timedelta(minutes=minutos * 1.5)
        if seguida:
            actual.append(revision)
        else:
            actual = [revision]
            incidentes.append(actual)
    return [(grupo[0].momento, len(grupo), len(grupo) * minutos) for grupo in incidentes]


def resumir(revisiones, desde, hasta, minutos):
    """Resumen del periodo con las revisiones en horario de atención."""
    del_periodo = [r for r in revisiones if desde <= r.momento.date() <= hasta and en_horario(r.momento)]
    total = len(del_periodo)
    fallidas = sum(not r.arriba for r in del_periodo)
    laborales = horas_laborales(desde, hasta)
    monitoreadas = total * minutos / 60
    porcentaje = (fallidas / total * 100) if total else None
    tiempos = sorted(r.milisegundos for r in del_periodo if r.arriba)
    por_dia = {}
    for r in del_periodo:
        dia = por_dia.setdefault(r.momento.date(), [0, 0])
        dia[0] += 1
        dia[1] += not r.arriba
    return {
        "desde": desde,
        "hasta": hasta,
        "revisiones": total,
        "caidas": fallidas,
        "horas_laborales": laborales,
        "horas_monitoreadas": monitoreadas,
        "cobertura": (monitoreadas / laborales * 100) if laborales else 0,
        "porcentaje_caida": porcentaje,
        "cumple": porcentaje is not None and porcentaje < META_CAIDA,
        "mediana_ms": tiempos[len(tiempos) // 2] if tiempos else None,
        "por_dia": sorted(por_dia.items()),
        "incidentes": caidas(del_periodo, minutos),
    }


def a_markdown(resumen, minutos):
    r = resumen
    caida = "—" if r["porcentaje_caida"] is None else f"{r['porcentaje_caida']:.2f} %"
    mediana = "—" if r["mediana_ms"] is None else f"{r['mediana_ms']} ms"
    resultado = (
        "Sin revisiones todavía"
        if r["porcentaje_caida"] is None
        else ("Cumple" if r["cumple"] else "NO CUMPLE")
    )
    lineas = [
        "# TS-08 · Disponibilidad en el horario de atención (RNF-06)",
        "",
        "Generado por `python scripts/monitor.py reporte` (S5-10). Medición en **periodo reducido**",
        f"(D-22): el monitor revisa `/salud/` cada {minutos} min de lunes a sábado de 9:00 a 19:00 mientras",
        "el equipo está encendido; las horas sin revisión no cuentan como caída ni como disponibilidad",
        "(se reporta la cobertura).",
        "El mes completo de la Tabla 4.15 sigue en operación después de `v1.0`.",
        "",
        "| Dato | Valor |",
        "|---|---|",
        f"| Periodo | {r['desde']:%d/%m/%Y} a {r['hasta']:%d/%m/%Y} |",
        f"| Horas laborales del periodo | {r['horas_laborales']} |",
        f"| Horas monitoreadas | {r['horas_monitoreadas']:.1f} ({r['cobertura']:.0f} % de cobertura) |",
        f"| Revisiones | {r['revisiones']} · {r['caidas']} con caída |",
        f"| Caída sobre lo monitoreado | {caida} (meta < {META_CAIDA:.0f} %) |",
        f"| Respuesta típica (mediana) | {mediana} |",
        f"| Resultado | **{resultado}** |",
        "",
        "## Por día",
        "",
        "| Día | Revisiones | Con caída | Caída |",
        "|---|---:|---:|---:|",
    ]
    for dia, (total, fallidas) in r["por_dia"]:
        porcentaje = fallidas / total * 100
        lineas.append(f"| {DIAS[dia.weekday()]} {dia:%d/%m/%Y} | {total} | {fallidas} | {porcentaje:.1f} % |")
    lineas += ["", "## Caídas", ""]
    if r["incidentes"]:
        lineas += ["| Inicio | Revisiones seguidas | Duración estimada |", "|---|---:|---:|"]
        lineas += [f"| {inicio:%d/%m/%Y %H:%M} | {n} | {mins} min |" for inicio, n, mins in r["incidentes"]]
    else:
        lineas.append("Sin caídas en el periodo.")
    return "\n".join(lineas) + "\n"


def reporte(args):
    revisiones = leer()
    if not revisiones and not (args.desde and args.hasta):
        sys.exit(f"Todavía no hay revisiones en {ARCHIVO.relative_to(RAIZ)}.")
    desde = args.desde or min(r.momento.date() for r in revisiones)
    hasta = args.hasta or max(r.momento.date() for r in revisiones)
    resumen = resumir(revisiones, desde, hasta, intervalo())
    REPORTE.write_text(a_markdown(resumen, intervalo()), encoding="utf-8")
    caida = "—" if resumen["porcentaje_caida"] is None else f"{resumen['porcentaje_caida']:.2f} %"
    print(
        f"TS-08 del {desde:%d/%m} al {hasta:%d/%m}: {resumen['revisiones']} revisiones, "
        f"{resumen['horas_monitoreadas']:.1f} h monitoreadas, caída {caida}. "
        f"Reporte en {REPORTE.relative_to(RAIZ)}"
    )
    return 0


def main(argv=None):
    cargar_env()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="accion", required=True)
    r = sub.add_parser("revisar", help="una revisión de /salud/ (solo en horario de atención)")
    r.add_argument("--forzar", action="store_true", help="revisar aunque sea fuera de horario")
    r.set_defaults(func=revisar)
    t = sub.add_parser("reporte", help="resumen del periodo para TS-08")
    t.add_argument("--desde", type=date.fromisoformat)
    t.add_argument("--hasta", type=date.fromisoformat)
    t.set_defaults(func=reporte)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
