#!/usr/bin/env python3
"""S5-13 · TS-05: tiempo de las búsquedas con más de 1,000 mascotas, medido en https://dogtor.local (RNF-05).

Criterio de la Tabla 4.15: respuesta en 2 segundos o menos. Cada búsqueda se repite 10 veces con la cuenta
que la usa en el día a día; se mide el tiempo completo (petición, consulta a la base y página recibida).

    python tests/carga/ts05_busquedas.py

Deja el resultado en docs/gestion/carga/ts05_resultado.md y sale con código 0 solo si todas cumplen.
"""

import json
import statistics
import sys
import time
from datetime import datetime

import requests
from comun import CARGA, HOST, LIMITE_MS, REPORTES, certificado, contrasena, token  # tests/carga

REPETICIONES = 10
# (cuenta, qué se busca, dirección, parámetros)
BUSQUEDAS = [
    ("recepcion", "Cliente por nombre", "/clientes/", {"q": "María"}),
    ("recepcion", "Cliente por apellido sin acento", "/clientes/", {"q": "martinez"}),
    ("recepcion", "Cliente por nombre y apellido", "/clientes/", {"q": "ana lopez"}),
    ("recepcion", "Cliente por teléfono", "/clientes/", {"q": "8330000"}),
    ("recepcion", "Cliente por nombre de mascota", "/clientes/", {"q": "Firulais"}),
    ("recepcion", "Cliente sin coincidencias", "/clientes/", {"q": "Zzyzx"}),
    ("recepcion", "Cliente para un ticket", "/ventas/nuevo/", {"q": "Luis"}),
    ("administrador", "Producto por nombre", "/inventario/productos/", {"q": "vacuna"}),
    ("administrador", "Producto por código", "/inventario/productos/", {"q": "ALI-001"}),
    ("administrador", "Productos con alerta", "/inventario/productos/", {"alerta": "stock_bajo"}),
    ("administrador", "Clientes dados de baja incluidos", "/clientes/", {"q": "José", "bajas": "1"}),
]


def sesion(cuenta):
    s = requests.Session()
    s.verify = certificado()
    s.headers["Referer"] = f"{HOST}/"
    formulario = s.get(f"{HOST}/cuenta/entrar/", timeout=30)
    datos = {
        "csrfmiddlewaretoken": token(formulario.text),
        "nombre_usuario": cuenta,
        "contrasena": contrasena(),
    }
    respuesta = s.post(f"{HOST}/cuenta/entrar/", data=datos, timeout=30)
    if "/cuenta/entrar/" in respuesta.url:
        sys.exit(f"No se pudo entrar como {cuenta}: revise DATOS_PRUEBA_CONTRASENA en .env.")
    return s


def medir(s, ruta, parametros):
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        respuesta = s.get(f"{HOST}{ruta}", params=parametros, timeout=30)
        tiempos.append((time.perf_counter() - inicio) * 1000)
        respuesta.raise_for_status()
    return tiempos


def main():
    mascotas = json.loads(CARGA.read_text(encoding="utf-8")).get("mascotas") if CARGA.exists() else None
    sesiones = {}
    filas = []
    for cuenta, que, ruta, parametros in BUSQUEDAS:
        sesiones.setdefault(cuenta, sesion(cuenta))
        tiempos = medir(sesiones[cuenta], ruta, parametros)
        filas.append((que, ruta, parametros, statistics.median(tiempos), max(tiempos)))
        print(f"{que:<38} mediana {statistics.median(tiempos):7.0f} ms · máximo {max(tiempos):7.0f} ms")
    cumple = all(maximo <= LIMITE_MS for *_, maximo in filas)
    lineas = [
        "# TS-05 · Tiempo de búsqueda con más de 1,000 mascotas (RNF-05)",
        "",
        "Generado por `python tests/carga/ts05_busquedas.py` (S5-13) contra el entorno con https (D-25). "
        "Criterio de la Tabla 4.15: 2 segundos o menos. Cada búsqueda se repite 10 veces; el tiempo incluye "
        "la página completa.",
        "",
        "| Dato | Valor |",
        "|---|---|",
        f"| Fecha | {datetime.now():%Y-%m-%d %H:%M} |",
        f"| Servidor | {HOST} |",
        f"| Mascotas en la base | {mascotas:,} |" if mascotas else "| Mascotas en la base | — |",
        f"| Búsqueda más lenta | {max(f[4] for f in filas):,.0f} ms |",
        f"| Resultado | **{'Cumple' if cumple else 'NO CUMPLE'}** |",
        "",
        "| Búsqueda | Pantalla | Mediana (ms) | Máximo (ms) | ≤ 2 s |",
        "|---|---|---:|---:|:---:|",
    ]
    lineas += [
        f"| {que} | `{ruta}` | {mediana:,.0f} | {maximo:,.0f} | {'Sí' if maximo <= LIMITE_MS else '**No**'} |"
        for que, ruta, _, mediana, maximo in filas
    ]
    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / "ts05_resultado.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"TS-05: {'Cumple' if cumple else 'NO CUMPLE'} · detalle en docs/gestion/carga/ts05_resultado.md")
    return 0 if cumple else 1


if __name__ == "__main__":
    sys.exit(main())
