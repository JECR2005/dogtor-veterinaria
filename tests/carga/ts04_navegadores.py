#!/usr/bin/env python3
"""S5-15 · TS-04: flujos principales en Chrome, Edge y una tableta de 10" e impresión en carta (RNF-02, D-27).

Criterio de la Tabla 4.15: los flujos funcionan en los tres equipos y la impresión sale correcta en carta.
Con Playwright, contra https://dogtor.local (D-25) y los datos de `preparar_carga`:

    python tests/carga/ts04_navegadores.py            # sin ventanas
    python tests/carga/ts04_navegadores.py --ver      # mirando cada navegador

Navegadores: Google Chrome y Microsoft Edge instalados en la laptop, y Chromium con la pantalla, el tacto y el
agente de una tableta Galaxy Tab S4 (10.5", horizontal). Flujos (RNF-07: agendar, consultar y cobrar):

- Recepción: buscar un cliente, agendar una cita, ver el calendario, imprimir la agenda del día, generar y
  cobrar un ticket, y su PDF.
- Veterinario: consultas del día, guardar una consulta, emitir una receta y su PDF, historial.
- Estilista: su agenda de estética.

En cada pantalla revisa además que no haya desplazamiento horizontal (diseño adaptable). Los PDF deben medir
carta: 612 × 792 puntos (la agenda, en horizontal). Deja docs/gestion/navegadores/ts04_resultado.md y capturas
en logs/ts04/. Sale con código 0 solo si todo pasa en los navegadores instalados.
"""

import argparse
import base64
import json
import re
import sys
from datetime import datetime, timedelta
from io import BytesIO

from comun import CARGA, HOST, RAIZ, certificado, contrasena  # tests/carga
from playwright.sync_api import Error as ErrorPlaywright
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

REPORTE = RAIZ / "docs" / "gestion" / "navegadores" / "ts04_resultado.md"
CAPTURAS = RAIZ / "logs" / "ts04"
NAVEGADORES = [
    ("Chrome", {"channel": "chrome"}, None),
    ("Edge", {"channel": "msedge"}, None),
    ('Tableta 10" (Galaxy Tab S4)', {}, "Galaxy Tab S4 landscape"),
]
CARTA, CARTA_HORIZONTAL = (612.0, 792.0), (792.0, 612.0)
ESPERA = 15_000


def tamano_pdf(contenido):
    pagina = PdfReader(BytesIO(contenido)).pages[0]
    return float(pagina.mediabox.width), float(pagina.mediabox.height)


def dia_habil(desde, dias):
    dia = desde + timedelta(days=dias)
    while dia.weekday() == 6:  # el domingo no hay servicio
        dia += timedelta(days=1)
    return dia


class Recorrido:
    """Un navegador: ejecuta cada paso, guarda su resultado y una captura, y revisa los desbordes."""

    def __init__(self, nombre, numero, navegador, ajustes):
        self.nombre, self.numero, self.navegador, self.ajustes = nombre, numero, navegador, ajustes
        self.resultados = {}
        self.desbordes = set()

    def pagina(self, cuenta):
        """Cada rol en su propia sesión (como otro equipo); si no puede entrar, lo anota y devuelve None."""
        pagina = self.navegador.new_context(**self.ajustes).new_page()
        pagina.set_default_timeout(ESPERA)

        def entrar(p):
            p.goto(f"{HOST}/cuenta/entrar/")
            p.fill('input[name="nombre_usuario"]', cuenta)
            p.fill('input[name="contrasena"]', contrasena())
            p.click('form button[type="submit"]')
            p.wait_for_url(lambda url: "/cuenta/entrar/" not in url)
            return "con certificado válido"

        self.paso(f"Inicio de sesión ({cuenta})", pagina, entrar)
        return pagina if self.resultados[f"Inicio de sesión ({cuenta})"][0] else None

    def pdf(self, pagina, ruta):
        """Descarga un PDF con el navegador (usa la sesión y confía en el certificado como el usuario)."""
        estado, contenido = pagina.evaluate(
            """async ruta => {
                const r = await fetch(ruta, {credentials: "same-origin"});
                const bytes = new Uint8Array(await r.arrayBuffer());
                let texto = "";
                for (let i = 0; i < bytes.length; i += 8192) {
                    texto += String.fromCharCode(...bytes.subarray(i, i + 8192));
                }
                return [r.status, btoa(texto)];
            }""",
            ruta,
        )
        assert estado == 200, f"HTTP {estado}"
        return base64.b64decode(contenido)

    def revisar(self, pagina):
        if not pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"):
            self.desbordes.add(re.sub(r"\d+", "<id>", pagina.url.replace(HOST, "")))

    def paso(self, nombre, pagina, funcion):
        try:
            detalle = funcion(pagina) or ""
            self.revisar(pagina)
            self.resultados[nombre] = (True, detalle)
        except (ErrorPlaywright, AssertionError, ValueError) as error:
            self.resultados[nombre] = (False, str(error).splitlines()[0][:160])
        CAPTURAS.mkdir(parents=True, exist_ok=True)
        archivo = re.sub(r"\W+", "_", f"{self.nombre}_{nombre}").strip("_").lower()
        try:
            pagina.screenshot(path=str(CAPTURAS / f"{archivo}.png"), full_page=True)
        except ErrorPlaywright:
            pass
        estado = "OK" if self.resultados[nombre][0] else "FALLA"
        print(f"  [{estado:5}] {nombre}: {self.resultados[nombre][1]}")


def recepcion(r, datos):
    cliente = datos["clientes"][r.numero]
    pagina = r.pagina("recepcion")
    if pagina is None:
        return

    def buscar(p):
        p.goto(f"{HOST}/clientes/?q=Ana")
        filas = p.locator("table tbody tr").count()
        assert filas > 0, "la búsqueda no mostró clientes"
        return f"{filas} clientes en la página"

    def agendar(p):
        p.goto(f"{HOST}/clientes/{cliente}/")
        p.goto(HOST + p.locator('a[href*="/clientes/mascotas/"]').first.get_attribute("href"))
        p.click('a:has-text("Agendar cita")')
        valor = p.eval_on_selector(
            "#id_servicio_elegir",
            "s => [...s.options].find(o => o.text.startsWith('Consulta general')).value",
        )
        with p.expect_navigation():
            p.select_option("#id_servicio_elegir", valor)
        p.select_option('select[name="empleado"]', index=1)
        fecha = dia_habil(datetime.now().date(), 21 + r.numero)
        for minutos in range(9 * 60, 18 * 60 + 1, 30):
            hora = f"{minutos // 60:02d}:{minutos % 60:02d}"
            p.fill('input[name="fecha"]', fecha.isoformat())
            p.fill('input[name="hora"]', hora)
            p.fill('[name="motivo"]', f"TS-04 en {r.nombre}")
            p.click('button:has-text("Agendar")')
            p.wait_for_load_state()
            if "Cita agendada" in p.content():
                return f"{fecha:%d/%m/%Y} {hora}"
        raise AssertionError("no encontró un horario libre")

    def calendario(p):
        p.goto(f"{HOST}/agenda/")
        p.wait_for_selector(".fc-view-harness")
        return "FullCalendar se dibujó"

    def agenda_pdf(p):
        p.goto(f"{HOST}/agenda/dia/")
        tamano = tamano_pdf(r.pdf(p, p.locator("[data-agenda-pdf]").get_attribute("href")))
        assert tamano == CARTA_HORIZONTAL, f"mide {tamano}"
        return "carta horizontal"

    def cobrar(p):
        p.goto(f"{HOST}/ventas/nuevo/?cliente={cliente}")
        p.select_option('select[name="lineas-0-articulo"]', datos["producto"])
        p.fill('input[name="lineas-0-cantidad"]', "1")
        p.select_option('select[name="lineas-1-articulo"]', datos["servicio"])
        p.fill('input[name="lineas-1-cantidad"]', "1")
        p.click('button:has-text("Generar ticket")')
        p.wait_for_url(re.compile(r".*/ventas/tickets/\d+/$"))
        p.check('input[name="metodo"][value="Efectivo"]')
        p.fill('input[name="recibido"]', "1000")
        p.click('button:has-text("Registrar pago")')
        p.wait_for_load_state()
        assert "Pagada" in p.content(), "el ticket no quedó pagado"
        return re.search(r"T-\d{4}-\d{5}", p.content()).group(0)

    def ticket_pdf(p):
        href = p.locator('a:has-text("PDF para imprimir")').get_attribute("href")
        tamano = tamano_pdf(r.pdf(p, href))
        assert tamano == CARTA, f"mide {tamano}"
        return "carta vertical"

    for nombre, funcion in [
        ("Buscar cliente", buscar),
        ("Agendar cita", agendar),
        ("Calendario", calendario),
        ("Agenda impresa (PDF)", agenda_pdf),
        ("Generar y cobrar ticket", cobrar),
        ("Ticket en PDF", ticket_pdf),
    ]:
        r.paso(nombre, pagina, funcion)


def veterinario(r, datos):
    consulta = datos["consultas"][r.numero % len(datos["consultas"])]
    pagina = r.pagina("veterinario")
    if pagina is None:
        return

    def dia(p):
        p.goto(f"{HOST}/clinica/")
        return "lista del día"

    def guardar(p):
        p.goto(f"{HOST}/clinica/consultas/{consulta['id']}/")
        p.fill('textarea[name="sintomas"]', f"Revisión TS-04 en {r.nombre}")
        p.locator('form:has(textarea[name="sintomas"]) button[type="submit"]').click()
        p.wait_for_load_state()
        assert "Consulta guardada." in p.content(), "no apareció «Consulta guardada.»"
        return "guardada"

    def receta(p):
        p.goto(f"{HOST}/clinica/consultas/{consulta['id']}/receta/")
        p.select_option('select[name="medicamentos-0-producto"]', index=1)
        p.fill('input[name="medicamentos-0-dosis"]', "1 tableta")
        p.fill('input[name="medicamentos-0-frecuencia"]', "Cada 12 horas")
        p.fill('input[name="medicamentos-0-duracion_dias"]', "5")
        p.locator('form:has(select[name="medicamentos-0-producto"]) button[type="submit"]').click()
        p.wait_for_url(re.compile(rf".*/clinica/consultas/{consulta['id']}/$"))
        href = p.locator('[data-receta] a[href$="/pdf/"]').last.get_attribute("href")
        tamano = tamano_pdf(r.pdf(p, href))
        assert tamano == CARTA, f"mide {tamano}"
        return "receta en carta vertical"

    def historial(p):
        p.goto(f"{HOST}/clinica/mascotas/{consulta['mascota']}/historial/")
        return "línea de tiempo"

    for nombre, funcion in [
        ("Consultas del día", dia),
        ("Guardar consulta", guardar),
        ("Receta en PDF", receta),
        ("Historial", historial),
    ]:
        r.paso(nombre, pagina, funcion)


def estilista(r, _datos):
    pagina = r.pagina("estilista")
    if pagina is None:
        return

    def agenda(p):
        p.goto(f"{HOST}/estetica/")
        return "agenda de estética"

    r.paso("Agenda de estética", pagina, agenda)


def reporte(columnas):
    pasos = list(dict.fromkeys(p for c in columnas.values() if c for p in c.resultados))
    lineas = [
        "# TS-04 · Navegadores, tableta e impresión (RNF-02)",
        "",
        "Generado por `python tests/carga/ts04_navegadores.py` (S5-15, D-27) contra el entorno con https",
        "(D-25). Criterio de la Tabla 4.15: los flujos funcionan en los tres equipos y la impresión sale en",
        "tamaño carta.",
        "",
        f"Fecha: {datetime.now():%Y-%m-%d %H:%M}. ✅ funciona · ❌ falla (con el motivo) · — no instalado.",
        "",
        "| Flujo | " + " | ".join(columnas) + " |",
        "|---|" + "---|" * len(columnas),
    ]
    for paso in pasos:
        celdas = []
        for recorrido in columnas.values():
            if recorrido is None:
                celdas.append("—")
            else:
                ok, detalle = recorrido.resultados.get(paso, (False, "no se ejecutó"))
                celdas.append(f"✅ {detalle}" if ok else f"❌ {detalle}")
        lineas.append(f"| {paso} | " + " | ".join(celdas) + " |")
    desbordes = [
        f"{n}: {', '.join(sorted(r.desbordes)) or 'ninguno'}" for n, r in columnas.items() if r is not None
    ]
    lineas += ["", "**Pantallas con desplazamiento horizontal:** " + "; ".join(desbordes) + "."]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main():
    opciones = argparse.ArgumentParser(description="TS-04 con Playwright")
    opciones.add_argument("--ver", action="store_true", help="mostrar las ventanas de los navegadores")
    ver = opciones.parse_args().ver
    if not CARGA.exists():
        sys.exit("Falta logs/carga.json: ejecute python manage.py preparar_carga")
    datos = json.loads(CARGA.read_text(encoding="utf-8"))
    columnas = {}
    with sync_playwright() as pw:
        for numero, (nombre, lanzar, dispositivo) in enumerate(NAVEGADORES):
            print(f"\n{nombre}")
            try:
                navegador = pw.chromium.launch(headless=not ver, **lanzar)
            except ErrorPlaywright:
                print("  no está instalado en este equipo")
                columnas[nombre] = None
                continue
            ajustes = {**(pw.devices[dispositivo] if dispositivo else {}), "locale": "es-MX"}
            recorrido = Recorrido(nombre, numero, navegador, ajustes)
            for flujo in (recepcion, veterinario, estilista):
                flujo(recorrido, datos)
            columnas[nombre] = recorrido
            navegador.close()
    reporte(columnas)
    probados = [r for r in columnas.values() if r is not None]
    todo_bien = (
        len(probados) == len(NAVEGADORES)
        and all(ok for r in probados for ok, _ in r.resultados.values())
        and not any(r.desbordes for r in probados)
    )
    resultado = "Cumple" if todo_bien else "revisar"
    print(f"\nTS-04: {resultado} · detalle en docs/gestion/navegadores/ts04_resultado.md")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    certificado()  # comprueba que exista la autoridad de mkcert (los navegadores usan la de Windows)
    sys.exit(main())
