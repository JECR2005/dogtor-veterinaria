"""S5-14 · TS-06: 10 usuarios simultáneos guardan consultas y cobran durante 30 minutos (RNF-05, Tabla 4.15).

Criterio: 95 % de las operaciones en 2 segundos o menos y cero errores. Contra el entorno con https (D-25),
con los datos de `cargar_datos_prueba --mascotas 1200 --historial 30` y `preparar_carga`:

    locust -f tests/carga/locustfile.py --headless -u 10 -r 2 -t 30m --host https://dogtor.local ^
        --csv docs/gestion/carga/ts06 --html docs/gestion/carga/ts06.html

- Recepcionista (5): genera un ticket con un artículo y una consulta, lo cobra en efectivo, busca clientes y
  revisa la lista de tickets. Cada ticket baja una pieza del mismo lote (RD-05: bloqueo real entre usuarios).
- Veterinario (5): guarda su consulta abierta con datos nuevos (cada guardado deja su registro en la
  bitácora), abre el historial de la mascota y su lista del día.

Al terminar escribe docs/gestion/carga/ts06_resultado.md y sale con código 0 solo si cumple.
"""

import itertools
import json
import random
import re

from comun import CARGA, LIMITE_MS, REPORTES, certificado, contrasena, fraccion_hasta, token  # tests/carga
from locust import HttpUser, between, events, task

DATOS = json.loads(CARGA.read_text(encoding="utf-8")) if CARGA.exists() else {}
NOMBRES = ["Ana", "Luis", "María", "José", "Carmen", "Pedro", "Laura", "Jorge", "Sofía", "Miguel"]
LINEAS = {
    "lineas-TOTAL_FORMS": "6",
    "lineas-INITIAL_FORMS": "0",
    "lineas-MIN_NUM_FORMS": "6",
    "lineas-MAX_NUM_FORMS": "20",
}
_turno = itertools.count()


class Personal(HttpUser):
    abstract = True
    wait_time = between(1, 3)
    cuenta = ""

    def on_start(self):
        if not DATOS:
            raise RuntimeError("Falta logs/carga.json: ejecute python manage.py preparar_carga")
        self.client.verify = certificado()
        self.client.headers["Referer"] = f"{self.host}/"  # Django revisa el origen de los POST por https
        formulario = self.client.get("/cuenta/entrar/", name="Inicio de sesión (formulario)")
        datos = {
            "csrfmiddlewaretoken": token(formulario.text),
            "nombre_usuario": self.cuenta,
            "contrasena": contrasena(),
        }
        with self.client.post("/cuenta/entrar/", datos, name="Inicio de sesión", catch_response=True) as r:
            if "/cuenta/entrar/" in r.url:
                r.failure(f"No pudo entrar como {self.cuenta}")
        self.csrf = token(self.client.get("/", name="Inicio").text)


class Recepcionista(Personal):
    cuenta = "recepcion"

    @task(3)
    def cobrar(self):
        url = f"/ventas/nuevo/?cliente={random.choice(DATOS['clientes'])}"
        formulario = self.client.get(url, name="Ticket nuevo (formulario)")
        self.csrf = token(formulario.text) or self.csrf
        lineas = {
            **LINEAS,
            "csrfmiddlewaretoken": self.csrf,
            "lineas-0-articulo": DATOS["producto"],
            "lineas-0-cantidad": "1",
            "lineas-1-articulo": DATOS["servicio"],
            "lineas-1-cantidad": "1",
        }
        with self.client.post(url, lineas, name="Generar ticket", catch_response=True) as r:
            ticket = re.search(r"/ventas/tickets/(\d+)/$", r.url)
            if not ticket:
                r.failure("No se generó el ticket")
                return
        pago = {"csrfmiddlewaretoken": self.csrf, "metodo": "Efectivo", "recibido": "1000"}
        with self.client.post(
            f"/ventas/tickets/{ticket.group(1)}/pagar/", pago, name="Registrar pago", catch_response=True
        ) as r:
            if "Pagada" not in r.text:
                r.failure("El ticket no quedó pagado")

    @task(2)
    def buscar(self):
        self.client.get("/clientes/", params={"q": random.choice(NOMBRES)}, name="Buscar cliente")

    @task(1)
    def tickets(self):
        self.client.get("/ventas/", name="Lista de tickets")


class Veterinario(Personal):
    cuenta = "veterinario"

    def on_start(self):
        super().on_start()
        self.consulta = DATOS["consultas"][next(_turno) % len(DATOS["consultas"])]
        self.guardados = 0

    @task(3)
    def guardar_consulta(self):
        url = f"/clinica/consultas/{self.consulta['id']}/"
        pantalla = self.client.get(url, name="Consulta")
        self.csrf = token(pantalla.text) or self.csrf
        self.guardados += 1
        datos = {
            "csrfmiddlewaretoken": self.csrf,
            "sintomas": f"Revisión de seguimiento {self.guardados}",
            "peso_kg": f"{random.uniform(5, 30):.2f}",
            "temperatura_c": "38.5",
            "diagnostico": "En observación",
            "tratamiento": "Indicaciones generales",
            "observaciones": "",
        }
        with self.client.post(url, datos, name="Guardar consulta", catch_response=True) as r:
            if "Consulta guardada." not in r.text:
                r.failure("La consulta no se guardó")

    @task(1)
    def historial(self):
        self.client.get(
            f"/clinica/mascotas/{self.consulta['mascota']}/historial/", name="Historial de la mascota"
        )

    @task(1)
    def dia(self):
        self.client.get("/clinica/", name="Consultas del día")


@events.quitting.add_listener
def evaluar(environment, **_):
    """TS-06: 95 % en 2 s o menos y cero errores; deja el resultado en Markdown."""
    total = environment.stats.total
    if not total.num_requests:
        return
    rapidas = fraccion_hasta(total.response_times)
    cumple = rapidas >= 95 and total.num_failures == 0
    usuarios = getattr(environment.parsed_options, "num_users", None) or "—"
    lineas = [
        "# TS-06 · 10 usuarios simultáneos (RNF-05)",
        "",
        "Generado por `tests/carga/locustfile.py` (S5-14) contra el entorno con https (D-25). Criterio de la "
        "Tabla 4.15: 95 % de las operaciones en 2 s o menos y cero errores.",
        "",
        "| Dato | Valor |",
        "|---|---|",
        f"| Mascotas en la base | {DATOS.get('mascotas', '—'):,} |",
        f"| Usuarios | {usuarios} (recepcionistas y veterinarios) |",
        f"| Operaciones | {total.num_requests:,} |",
        f"| Errores | {total.num_failures} |",
        f"| En 2 s o menos | {rapidas:.2f} % |",
        f"| Percentil 95 | {total.get_response_time_percentile(0.95):,.0f} ms |",
        f"| Mediana · máximo | {total.median_response_time:,.0f} ms · {total.max_response_time:,.0f} ms |",
        f"| Operaciones por segundo | {total.total_rps:.2f} |",
        f"| Resultado | **{'Cumple' if cumple else 'NO CUMPLE'}** |",
        "",
        "| Operación | Veces | Errores | Mediana (ms) | P95 (ms) | Máximo (ms) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for (nombre, metodo), s in sorted(environment.stats.entries.items()):
        lineas.append(
            f"| {nombre} ({metodo}) | {s.num_requests:,} | {s.num_failures} | "
            f"{s.median_response_time:,.0f} | {s.get_response_time_percentile(0.95):,.0f} | "
            f"{s.max_response_time:,.0f} |"
        )
    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / "ts06_resultado.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    environment.process_exit_code = 0 if cumple else 1
    resultado = "Cumple" if cumple else "NO CUMPLE"
    print(f"TS-06: {rapidas:.2f} % en ≤ {LIMITE_MS} ms, {total.num_failures} errores · {resultado}")
