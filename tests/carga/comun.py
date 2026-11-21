"""Lo que comparten Locust (TS-06) y la medición de búsquedas (TS-05) contra https://dogtor.local (D-25).

No depende de Django: se ejecuta desde la laptop contra el entorno con https, como lo usaría el personal.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOST = os.environ.get("DOGTOR_HOST", "https://dogtor.local")
CARGA = RAIZ / "logs" / "carga.json"
REPORTES = RAIZ / "docs" / "gestion" / "carga"
LIMITE_MS = 2000  # RNF-05: 2 segundos o menos
TOKEN = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')


def leer_env():
    valores = {}
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip()
    return valores


def contrasena():
    """La de las cuentas ficticias (DATOS_PRUEBA_CONTRASENA de .env)."""
    return os.environ.get("DATOS_PRUEBA_CONTRASENA") or leer_env().get("DATOS_PRUEBA_CONTRASENA", "")


def certificado():
    """La autoridad de mkcert, para que las peticiones confíen en https://dogtor.local como el navegador."""
    if os.environ.get("DOGTOR_CA"):
        return os.environ["DOGTOR_CA"]
    mkcert = shutil.which("mkcert")
    if mkcert:
        carpeta = subprocess.run(
            [mkcert, "-CAROOT"], capture_output=True, text=True, check=False
        ).stdout.strip()
        raiz = Path(carpeta) / "rootCA.pem"
        if raiz.exists():
            return str(raiz)
    return True  # sin mkcert: los certificados del sistema


def token(html):
    encontrado = TOKEN.search(html or "")
    return encontrado.group(1) if encontrado else ""


def fraccion_hasta(tiempos, limite=LIMITE_MS):
    """Porcentaje de operaciones que tardaron `limite` ms o menos. `tiempos`: {ms: cuántas}."""
    total = sum(tiempos.values())
    return 100.0 * sum(n for ms, n in tiempos.items() if ms <= limite) / total if total else 0.0
