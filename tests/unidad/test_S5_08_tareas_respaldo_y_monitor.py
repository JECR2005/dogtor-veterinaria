"""S5-08 a S5-10 · Tareas programadas, TS-07 (comparación de registros) y TS-08 (monitor de /salud/).

Lo que corre en el Programador de tareas y contra SQL Server se prueba en la laptop (guion del bloque C);
aquí se prueban las reglas que lo deciden: horario de atención, cálculo de caídas, comparación de conteos
y bitácora de las tareas.
"""

import csv
import io
import json
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from scripts import monitor, respaldo, tarea

pytestmark = pytest.mark.unidad

LUNES = datetime(2026, 11, 23)  # lunes


# --- S5-10 · Horario de atención (RNF-06) -----------------------------------------------------------
@pytest.mark.parametrize(
    "momento, esperado",
    [
        (LUNES.replace(hour=9), True),
        (LUNES.replace(hour=18, minute=59), True),
        (LUNES.replace(hour=19), False),  # 19:00 ya cerró
        (LUNES.replace(hour=8, minute=59), False),
        (LUNES + timedelta(days=5, hours=12), True),  # sábado
        (LUNES + timedelta(days=6, hours=12), False),  # domingo
    ],
)
def test_S5_10_horario_de_atencion(momento, esperado):
    assert monitor.en_horario(momento) is esperado


def test_S5_10_horas_laborales_sin_domingo():
    assert monitor.horas_laborales(LUNES.date(), (LUNES + timedelta(days=6)).date()) == 60  # 6 días × 10 h


def _revision(minutos_desde_las_9, arriba=True, dia=0):
    momento = LUNES + timedelta(days=dia, hours=9, minutes=minutos_desde_las_9)
    return monitor.Revision(momento, arriba, 40, "" if arriba else "Sin respuesta")


def test_S5_10_resumen_con_una_caida_de_tres_revisiones_seguidas():
    revisiones = [_revision(m) for m in range(0, 600, 5)]  # lunes completo: 120 revisiones
    for i in (24, 25, 26):  # 11:00 a 11:10 sin respuesta
        revisiones[i] = _revision(i * 5, arriba=False)
    revisiones.append(_revision(-120))  # 7:00: fuera de horario, no cuenta
    revisiones.append(_revision(30, dia=1))  # martes, una revisión
    resumen = monitor.resumir(revisiones, LUNES.date(), (LUNES + timedelta(days=1)).date(), 5)
    assert (resumen["revisiones"], resumen["caidas"], resumen["horas_laborales"]) == (121, 3, 20)
    assert resumen["horas_monitoreadas"] == pytest.approx(121 * 5 / 60)
    assert resumen["porcentaje_caida"] == pytest.approx(3 / 121 * 100)
    assert not resumen["cumple"]  # 2.48 % > 1 %
    assert resumen["incidentes"] == [(LUNES.replace(hour=11), 3, 15)]
    assert [total for _, (total, _) in resumen["por_dia"]] == [120, 1]
    texto = monitor.a_markdown(resumen, 5)
    assert (
        "periodo reducido" in texto and "NO CUMPLE" in texto and "| 23/11/2026 11:00 | 3 | 15 min |" in texto
    )


def test_S5_10_sin_caidas_cumple_y_sin_revisiones_no_se_inventa_un_resultado():
    revisiones = [_revision(m) for m in range(0, 600, 5)]
    assert monitor.resumir(revisiones, LUNES.date(), LUNES.date(), 5)["cumple"]
    vacio = monitor.resumir([], LUNES.date(), LUNES.date(), 5)
    assert vacio["porcentaje_caida"] is None and not vacio["cumple"]
    assert "Sin revisiones todavía" in monitor.a_markdown(vacio, 5)


class _Salud(BaseHTTPRequestHandler):
    respuesta = (200, {"estado": "ok"})

    def do_GET(self):  # noqa: N802
        codigo, cuerpo = self.respuesta
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(cuerpo).encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def servidor():
    http = HTTPServer(("127.0.0.1", 0), _Salud)
    hilo = threading.Thread(target=http.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{http.server_port}/salud/"
    http.shutdown()


def test_S5_10_consultar_salud_arriba_caida_y_sin_respuesta(servidor, monkeypatch):
    monkeypatch.setattr(_Salud, "respuesta", (200, {"estado": "ok"}))
    assert monitor.consultar(servidor)[:2] == (monitor.ARRIBA, 200)
    monkeypatch.setattr(_Salud, "respuesta", (503, {"estado": "sin_base_de_datos"}))
    assert monitor.consultar(servidor)[:2] == (monitor.CAIDA, 503)
    resultado, codigo, _, detalle = monitor.consultar("http://127.0.0.1:9/salud/", espera=2)
    assert (resultado, codigo) == (monitor.CAIDA, 0) and detalle.startswith("Sin respuesta")


def test_S5_10_revisar_anota_en_el_csv_y_reporte_lo_lee(servidor, tmp_path, monkeypatch):
    archivo = tmp_path / "disponibilidad.csv"
    monkeypatch.setattr(monitor, "ARCHIVO", archivo)
    monkeypatch.setattr(monitor, "REPORTE", tmp_path / "reporte.md")
    monkeypatch.setattr(monitor, "RAIZ", tmp_path)
    monkeypatch.setenv("MONITOR_URL", servidor)
    assert monitor.main(["revisar", "--forzar"]) == 0
    filas = list(csv.DictReader(io.StringIO(archivo.read_text(encoding="utf-8"))))
    assert filas[0]["resultado"] == "Arriba" and filas[0]["codigo"] == "200"
    hoy = date.today().isoformat()
    assert monitor.main(["reporte", "--desde", hoy, "--hasta", hoy]) == 0
    assert "TS-08" in (tmp_path / "reporte.md").read_text(encoding="utf-8")


# --- S5-09 · TS-07: comparación de registros ------------------------------------------------------
def test_S5_09_comparar_detecta_tablas_distintas_o_faltantes():
    origen = {"dbo.cliente": 5, "dbo.venta": 3, "dbo.pago": 4}
    restaurada = {"dbo.cliente": 5, "dbo.venta": 2, "dbo.lote": 1}
    assert respaldo.comparar(origen, restaurada) == [
        ("dbo.cliente", 5, 5, True),
        ("dbo.lote", None, 1, False),
        ("dbo.pago", 4, None, False),
        ("dbo.venta", 3, 2, False),
    ]


def test_S5_09_detalle_de_ts07():
    filas = respaldo.comparar(
        {"dbo.cliente": 1200, "dbo.venta": 210}, {"dbo.cliente": 1200, "dbo.venta": 210}
    )
    texto = respaldo.detalle_ts07(
        {
            "fecha": datetime(2026, 11, 22, 21, 0),
            "base": "Dogtor",
            "servidor_origen": "localhost",
            "servidor_limpio": "localhost,14330",
            "version": "SQL Server 17.0 (Developer Edition)",
            "archivo": "Dogtor_2026-11-22_210000.bak",
            "tamano": "12.00 MB",
            "seg_respaldo": 0.4,
            "seg_restauracion": 2.5,
            "filas": filas,
            "resultado": "Cumple",
            "ejecuto": "JECR2005",
        }
    )
    assert "| Tablas | 2 · 2 con el mismo número de registros |" in texto
    assert "1,410 en el origen · 1,410 restaurados" in texto and "**Cumple**" in texto
    assert "| `dbo.venta` | 210 | 210 | Sí |" in texto


def test_S5_09_el_registro_de_restauraciones_conserva_sus_nueve_columnas(tmp_path, monkeypatch):
    registro = tmp_path / "docs" / "registro.md"
    registro.parent.mkdir(parents=True)
    monkeypatch.setattr(respaldo, "REGISTRO", registro)
    monkeypatch.setattr(respaldo, "RAIZ", tmp_path)
    respaldo.anotar("P5", "`a.bak`", "1.00 MB", 0.5, 2.0, "33, conteos iguales", "Cumple", "JECR2005")
    lineas = registro.read_text(encoding="utf-8").splitlines()
    assert lineas[4].count("|") == lineas[-1].count("|") == 10  # encabezado y fila: 9 columnas


# --- S5-08 · Tareas programadas ---------------------------------------------------------------------
def test_S5_08_las_tareas_usan_python_de_consola_y_dejan_bitacora(tmp_path):
    assert set(tarea.COMANDOS) == {"respaldo", "recordatorios", "monitor"}
    assert tarea.COMANDOS["recordatorios"] == ["manage.py", "generar_recordatorios"]
    pythonw = tmp_path / "pythonw.exe"
    (tmp_path / "python.exe").write_text("")
    assert tarea.python_de_consola(str(pythonw)) == str(tmp_path / "python.exe")
    assert tarea.python_de_consola("/usr/bin/python3") == "/usr/bin/python3"

    log = tmp_path / "logs" / "tareas.log"
    tarea.registrar("respaldo", 1, "Error 3201\nNo se pudo abrir", datetime(2026, 11, 22, 22, 0), log)
    assert log.read_text(encoding="utf-8").splitlines() == [
        "[2026-11-22 22:00:00] respaldo: FALLÓ (código 1)",
        "    Error 3201",
        "    No se pudo abrir",
    ]


def test_S5_08_una_tarea_desconocida_se_rechaza():
    with pytest.raises(SystemExit, match="Tarea desconocida"):
        tarea.ejecutar("borrar")


def test_S5_08_la_copia_externa_acepta_variables_de_entorno(tmp_path, monkeypatch):
    """%USERPROFILE%\\OneDrive\\… en .env: la copia externa llega a la carpeta de OneDrive del usuario."""
    origen, nube = tmp_path / "respaldos", tmp_path / "perfil"
    origen.mkdir()
    monkeypatch.setenv("PERFIL_PRUEBA", str(nube))
    monkeypatch.setenv("RESPALDO_DIR", str(origen))
    monkeypatch.setenv("RESPALDO_COPIA_EXTERNA", "$PERFIL_PRUEBA/copia")  # en Windows: %USERPROFILE%\\...
    monkeypatch.setattr(respaldo, "conectar", lambda *a, **k: _ConexionFalsa(origen))
    archivo, _ = respaldo.respaldar(None)
    assert (nube / "copia" / archivo.name).exists()


class _ConexionFalsa:
    """Simula BACKUP DATABASE: crea el archivo que pide la instrucción."""

    def __init__(self, carpeta):
        self.carpeta = carpeta

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        class Cursor:
            description = None

            def execute(self, sql, *parametros):
                if sql.startswith("BACKUP"):
                    from pathlib import Path

                    Path(parametros[0]).write_bytes(b"respaldo")

            def nextset(self):
                return False

        return Cursor()
