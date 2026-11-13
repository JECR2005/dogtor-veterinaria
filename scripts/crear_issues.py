#!/usr/bin/env python3
"""S0-02 · Crea en GitHub el backlog del proyecto: un issue por requisito.

Lee docs/gestion/backlog.csv (RF-01 a RF-14, RD-01 a RD-12, RNF-01 a RNF-08) y,
con la CLI de GitHub (gh), crea:
  - las etiquetas de tipo (RF, RD, RNF), prioridad y componente;
  - un milestone por prototipo (P1 a P5);
  - un issue por requisito con su criterio de aceptación como lista de verificación.

Uso (desde la raíz del repositorio, con `gh auth login` hecho):
    python scripts/crear_issues.py --repo USUARIO/dogtor --dry-run   # solo muestra
    python scripts/crear_issues.py --repo USUARIO/dogtor             # crea

Justificación: trazabilidad del 100 % (Tabla 3.20) y área RDM de CMMI (Tabla 3.18).
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BACKLOG = RAIZ / "docs" / "gestion" / "backlog.csv"

PROTOTIPOS = {
    "P1": "Núcleo de operación: clientes, mascotas, empleados, servicios y citas",
    "P2": "Abastecimiento: productos, lotes, alertas, proveedores y pedidos",
    "P3": "Núcleo clínico y estética: consultas, recetas, aplicaciones, recordatorios",
    "P4": "Ventas y caja: tickets, pagos parciales, cancelaciones y corte",
    "P5": "Integración y endurecimiento: bitácora, respaldos, rendimiento, aceptación",
}
COLORES = {"RF": "1d76db", "RD": "d93f0b", "RNF": "5319e7", "Alta": "b60205", "Media": "fbca04"}


def gh(args, dry_run, permitir_error=False):
    print("  $ gh " + " ".join(args))
    if dry_run:
        return ""
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0 and not permitir_error:
        sys.exit(f"Error: {r.stderr.strip()}")
    return r.stdout


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", required=True, help="USUARIO/REPOSITORIO en GitHub")
    p.add_argument("--dry-run", action="store_true", help="muestra los comandos sin ejecutarlos")
    a = p.parse_args()

    filas = list(csv.DictReader(BACKLOG.open(encoding="utf-8")))
    print(f"Backlog: {len(filas)} requisitos")

    print("\n1. Etiquetas")
    etiquetas = {"RF", "RD", "RNF", "Alta", "Media"} | {f"comp:{f['componente']}" for f in filas}
    for e in sorted(etiquetas):
        color = COLORES.get(e, "c5def5")
        gh(["label", "create", e, "--repo", a.repo, "--color", color, "--force"], a.dry_run)

    print("\n2. Milestones (un prototipo = un milestone)")
    existentes = set()
    if not a.dry_run:
        salida = gh(["api", f"repos/{a.repo}/milestones?state=all&per_page=100"], False, permitir_error=True)
        existentes = {m["title"] for m in json.loads(salida or "[]")}
    for clave, desc in PROTOTIPOS.items():
        if clave in existentes:
            print(f"  (ya existe {clave})")
            continue
        gh(
            ["api", f"repos/{a.repo}/milestones", "-f", f"title={clave}", "-f", f"description={desc}"],
            a.dry_run,
        )

    print("\n3. Issues (API REST)")
    numeros = {}
    if not a.dry_run:
        salida = gh(["api", f"repos/{a.repo}/milestones?state=all&per_page=100"], False)
        numeros = {m["title"]: m["number"] for m in json.loads(salida or "[]")}
        salida = gh(["api", f"repos/{a.repo}/issues?state=all&per_page=100"], False)
        ya = {i["title"].split(" ")[0] for i in json.loads(salida or "[]")}
    else:
        ya = set()
    for f in filas:
        if f["id"] in ya:
            print(f"  (ya existe {f['id']})")
            continue
        primer_prototipo = f["prototipo"].split(",")[0]
        cuerpo = (
            f"**Requisito:** {f['id']} · {f['titulo']}\n"
            f"**Tipo:** {f['tipo']} · **Prioridad:** {f['prioridad']} · "
            f"**Prototipo:** {f['prototipo']} · **Componente:** `{f['componente']}`\n\n"
            "### Criterio de aceptación (apartado 3.2.2)\n"
            f"- [ ] {f['criterio_aceptacion']}\n\n"
            "### Trazabilidad (Tabla 3.59)\n"
            "- [ ] Caso(s) de uso revisados\n"
            "- [ ] Caso(s) de prueba TU/TI/TA/TS que lo verifican\n"
            + (
                "- [ ] Prueba que intenta violar la regla (meta 100 % de RD, Tabla 3.20)\n"
                if f["tipo"] == "RD"
                else ""
            )
        )
        datos = {
            "title": f"{f['id']} {f['titulo']}",
            "body": cuerpo,
            "labels": [f["tipo"], f["prioridad"], f"comp:{f['componente']}"],
            "milestone": numeros.get(primer_prototipo),
        }
        print(f"  {datos['title']} → {primer_prototipo}")
        if not a.dry_run:
            r = subprocess.run(
                ["gh", "api", "-X", "POST", f"repos/{a.repo}/issues", "--input", "-"],
                input=json.dumps(datos),
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                sys.exit(f"Error al crear {f['id']}: {r.stderr.strip()}")
    print("\nListo.")


if __name__ == "__main__":
    main()
