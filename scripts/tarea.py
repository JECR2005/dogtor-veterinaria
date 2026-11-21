#!/usr/bin/env python3
"""S5-08 · Punto de entrada de las tareas programadas de Windows (scripts/programar_tareas.ps1).

Uso (el Programador de tareas lo llama con pythonw.exe, sin abrir ventana):
    python scripts/tarea.py respaldo        # 22:00 diario: respaldo, copia externa y 30 días (RNF-04)
    python scripts/tarea.py recordatorios   # 08:30, lunes a sábado: recordatorios del día (RF-09)
    python scripts/tarea.py monitor         # cada 5 min, 9:00 a 19:00, lunes a sábado (RNF-06, TS-08)

Cada ejecución queda en logs/tareas.log con su salida; las revisiones del monitor que salen bien no, para
no llenarlo (esas ya están en logs/disponibilidad.csv). Si el paso falla, termina con código 1 y el
Programador de tareas lo muestra como «Último resultado» distinto de 0.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LOG = RAIZ / "logs" / "tareas.log"
COMANDOS = {
    "respaldo": ["scripts/respaldo.py", "respaldar"],
    "recordatorios": ["manage.py", "generar_recordatorios"],
    "monitor": ["scripts/monitor.py", "revisar"],
}
LIMITE_SEGUNDOS = 2 * 60 * 60


def python_de_consola(ejecutable=sys.executable):
    """pythonw.exe no tiene consola; los pasos se ejecutan con el python.exe del mismo entorno virtual."""
    ruta = Path(ejecutable)
    if ruta.name.lower() == "pythonw.exe" and ruta.with_name("python.exe").exists():
        return str(ruta.with_name("python.exe"))
    return str(ruta)


def registrar(nombre, codigo, salida, ahora=None, log=LOG):
    ahora = ahora or datetime.now()
    log.parent.mkdir(parents=True, exist_ok=True)
    estado = "OK" if codigo == 0 else f"FALLÓ (código {codigo})"
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{ahora:%Y-%m-%d %H:%M:%S}] {nombre}: {estado}\n")
        for linea in salida.strip().splitlines():
            f.write(f"    {linea}\n")


def ejecutar(nombre):
    if nombre not in COMANDOS:
        sys.exit(f"Tarea desconocida: {nombre}. Use una de: {', '.join(COMANDOS)}.")
    entorno = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        resultado = subprocess.run(  # noqa: S603 - comandos fijos del proyecto
            [python_de_consola(), *COMANDOS[nombre]],
            cwd=RAIZ,
            env=entorno,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=LIMITE_SEGUNDOS,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        codigo, salida = resultado.returncode, resultado.stdout + resultado.stderr
    except subprocess.TimeoutExpired:
        codigo, salida = 1, f"No terminó en {LIMITE_SEGUNDOS // 60} minutos."
    if not (nombre == "monitor" and codigo == 0):
        registrar(nombre, codigo, salida)
    return codigo


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(ejecutar(sys.argv[1]))
