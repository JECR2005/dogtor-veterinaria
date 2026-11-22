"""S5-13 y S5-14 · Cálculos compartidos de TS-05 y TS-06 (tests/carga/comun.py)."""

import pytest

from tests.carga import comun

pytestmark = pytest.mark.unidad


def test_S5_14_porcentaje_de_operaciones_en_2_segundos_o_menos():
    assert comun.fraccion_hasta({100: 90, 1900: 5, 2000: 1, 2100: 4}) == pytest.approx(96.0)
    assert comun.fraccion_hasta({}) == 0.0


def test_S5_14_toma_el_token_de_csrf_del_formulario():
    html = '<form><input type="hidden" name="csrfmiddlewaretoken" value="abc123"></form>'
    assert comun.token(html) == "abc123" and comun.token("<p>sin formulario</p>") == ""


def test_S5_14_la_contrasena_sale_del_entorno(monkeypatch):
    monkeypatch.setenv("DATOS_PRUEBA_CONTRASENA", "Clave-Prueba-2026")
    assert comun.contrasena() == "Clave-Prueba-2026"
    monkeypatch.setenv("DOGTOR_CA", "/ruta/rootCA.pem")
    assert comun.certificado() == "/ruta/rootCA.pem"


def test_S5_14_encuentra_la_autoridad_de_mkcert_aunque_mkcert_no_este_en_el_path(tmp_path, monkeypatch):
    (tmp_path / "mkcert").mkdir()
    (tmp_path / "mkcert" / "rootCA.pem").write_text("certificado")
    monkeypatch.delenv("DOGTOR_CA", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(comun.shutil, "which", lambda _: None)
    assert comun.certificado() == str(tmp_path / "mkcert" / "rootCA.pem")
