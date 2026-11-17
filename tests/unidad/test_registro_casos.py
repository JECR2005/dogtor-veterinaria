"""Tabla 4.19 · El registro de ejecución se arma bien desde el reporte JUnit (scripts/registro_casos.py)."""

import pytest

from scripts import registro_casos

pytestmark = pytest.mark.unidad

REPORTE = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest">
  <testcase classname="t" name="test_TU01_hay_empalme_y_aparece_el_mensaje"/>
  <testcase classname="t" name="test_TU02_terminar_justo_cuando_otra_inicia_no_es_empalme"/>
  <testcase classname="t" name="test_TU05_veterinario_sin_cedula_no_se_guarda[None]"/>
  <testcase classname="t" name="test_TU05_veterinario_con_cedula_si_se_guarda">
    <failure message="assert False"/>
  </testcase>
  <testcase classname="t" name="test_TI02_agendar_estetica"><skipped/></testcase>
  <testcase classname="t" name="test_sin_identificador"/>
</testsuite></testsuites>"""


@pytest.fixture
def reporte(tmp_path):
    ruta = tmp_path / "reporte.xml"
    ruta.write_text(REPORTE, encoding="utf-8")
    return ruta


def test_agrupa_las_pruebas_por_caso(reporte):
    casos = registro_casos.casos_del_reporte(reporte)
    assert list(casos) == ["TI-02", "TU-01", "TU-02", "TU-05"]
    assert casos["TU-05"] == {"pruebas": 2, "fallidas": 1, "omitidas": 0}


def test_resultado_de_cada_caso(reporte):
    casos = registro_casos.casos_del_reporte(reporte)
    assert registro_casos.resultado(casos["TU-01"]) == "Aprobado"
    assert registro_casos.resultado(casos["TU-05"]) == "Fallido"
    assert registro_casos.resultado(casos["TI-02"]) == "Bloqueado"


def test_la_tabla_tiene_las_columnas_de_la_tabla_4_19(reporte, capsys):
    assert registro_casos.main([str(reporte), "--version", "abc1234def"]) == 1  # hay un caso fallido
    salida = capsys.readouterr().out
    assert salida.startswith("| Caso | Fecha | Ejecutor | Versión")
    assert "| TU-01 |" in salida and "`abc1234`" in salida and "| Aprobado |" in salida
