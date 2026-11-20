"""S3-14 · Revisión en tableta (OBS-04, RNF-02, RI-09 y RI-10): reglas que se pueden comprobar en el código.

La revisión visual en la tableta se registra en docs/gestion/revision_tableta_P3.md; aquí se cuida que no
se pierda lo que la hace posible: ventana adaptable, tablas que se desplazan dentro de su caja y objetivos
táctiles de 44 px.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unidad

RAIZ = Path(__file__).resolve().parents[2]
PLANTILLAS = RAIZ / "templates"
# Los PDF (receta) no se ven en pantalla: tienen tamaño carta fijo
EXCLUIDAS = {"reportes"}


def _plantillas():
    for archivo in sorted(PLANTILLAS.rglob("*.html")):
        if archivo.relative_to(PLANTILLAS).parts[0] not in EXCLUIDAS:
            yield archivo


def test_S3_14_la_pagina_se_adapta_al_ancho_de_la_tableta():
    base = (PLANTILLAS / "base.html").read_text(encoding="utf-8")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in base


@pytest.mark.parametrize("archivo", list(_plantillas()), ids=lambda a: str(a.relative_to(PLANTILLAS)))
def test_S3_14_cada_tabla_se_desplaza_dentro_de_su_caja(archivo):
    """Sin esto, una tabla ancha empuja toda la pantalla de lado en la tableta vertical."""
    texto = archivo.read_text(encoding="utf-8")
    assert texto.count("<table") == texto.count("table-responsive")


def test_S3_14_objetivos_tactiles_y_menu_contraido():
    css = (RAIZ / "static" / "css" / "dogtor.css").read_text(encoding="utf-8")
    assert ".btn, .form-control, .form-select { min-height: 44px; }" in css  # RI-09
    assert "@media (max-width: 991.98px)" in css and ".dg-menu-texto { display: none; }" in css  # RI-10
    assert "@media (pointer: coarse)" in css  # casillas más grandes al tocar
