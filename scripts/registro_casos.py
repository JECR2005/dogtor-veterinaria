"""Tabla 4.19 · Registro de ejecución de casos a partir del reporte JUnit de pytest (S1-18 a S1-20).

Cada prueba cuyo nombre lleva el identificador del caso (test_TU05_..., test_TI01_..., test_TS01_...) cuenta
para ese caso. Un caso queda Aprobado si todas sus pruebas pasan, Fallido si alguna falla y Bloqueado si
alguna se omitió. Se usa en la integración continua para dejar la evidencia en el resumen del trabajo.

Uso: python scripts/registro_casos.py reporte-pruebas.xml --version <commit> [--ejecutor "CI"]
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

CASO = re.compile(r"test_(T[UIST])_?(\d{2})")


def casos_del_reporte(ruta):
    """{«TU-05»: {"pruebas": n, "fallidas": n, "omitidas": n}} a partir del XML de JUnit."""
    casos = defaultdict(lambda: {"pruebas": 0, "fallidas": 0, "omitidas": 0})
    for prueba in ET.parse(ruta).getroot().iter("testcase"):
        coincidencia = CASO.search(prueba.get("name", ""))
        if not coincidencia:
            continue
        caso = casos[f"{coincidencia.group(1)}-{coincidencia.group(2)}"]
        caso["pruebas"] += 1
        if prueba.find("failure") is not None or prueba.find("error") is not None:
            caso["fallidas"] += 1
        elif prueba.find("skipped") is not None:
            caso["omitidas"] += 1
    return dict(sorted(casos.items()))


def resultado(caso):
    if caso["fallidas"]:
        return "Fallido"
    if caso["omitidas"]:
        return "Bloqueado"
    return "Aprobado"


def tabla(casos, version, ejecutor, fecha):
    filas = [
        "| Caso | Fecha | Ejecutor | Versión (etiqueta/commit y entorno) | Resultado | Defecto | Evidencia |",
        "|---|---|---|---|---|---|---|",
    ]
    for nombre, caso in casos.items():
        evidencia = f"{caso['pruebas']} prueba(s) automatizada(s), reporte JUnit de la CI"
        filas.append(
            f"| {nombre} | {fecha:%d/%m/%Y} | {ejecutor} | `{version}` · CI (SQL Server 2022) "
            f"| {resultado(caso)} | | {evidencia} |"
        )
    return "\n".join(filas)


def main(argumentos=None):
    lector = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    lector.add_argument("reporte")
    lector.add_argument("--version", default="sin-commit")
    lector.add_argument("--ejecutor", default="CI (GitHub Actions)")
    datos = lector.parse_args(argumentos)
    casos = casos_del_reporte(datos.reporte)
    hoy = datetime.now(ZoneInfo("America/Monterrey")).date()  # fecha de la clínica, no la del servidor
    print(tabla(casos, datos.version[:7], datos.ejecutor, hoy))
    return 1 if any(resultado(c) == "Fallido" for c in casos.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
