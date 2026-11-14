"""S1-15 · La interfaz funciona sin internet (R07): nada viene de un CDN; todo está en static/vendor."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders

pytestmark = pytest.mark.integracion

PLANTILLAS = Path(settings.BASE_DIR) / "templates"
EXTERNO = re.compile(r"""(src|href)=["']https?://""")

COMPONENTES = [
    "vendor/bootstrap/css/bootstrap.min.css",
    "vendor/bootstrap/js/bootstrap.bundle.min.js",
    "vendor/bootstrap-icons/bootstrap-icons.min.css",
    "vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
    "vendor/bootstrap-icons/fonts/bootstrap-icons.woff",
    "vendor/fullcalendar/index.global.min.js",
    "vendor/fullcalendar/locales/es.global.min.js",
]


def test_S1_15_ninguna_plantilla_carga_recursos_de_internet():
    externos = [
        f"{ruta.relative_to(PLANTILLAS)}: {linea.strip()}"
        for ruta in PLANTILLAS.rglob("*.html")
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if EXTERNO.search(linea)
    ]
    assert externos == []


@pytest.mark.parametrize("archivo", COMPONENTES)
def test_S1_15_los_componentes_estan_en_el_proyecto(archivo):
    ruta = finders.find(archivo)
    assert ruta is not None, f"Falta {archivo}: ejecute scripts/traer_componentes.sh"
    assert Path(ruta).stat().st_size > 500  # el más pequeño es el idioma español (~0.7 KB)


@pytest.mark.parametrize(
    "licencia", ["bootstrap/LICENSE", "bootstrap-icons/LICENSE", "fullcalendar/LICENSE.md"]
)
def test_las_licencias_viajan_con_los_componentes(licencia):
    assert finders.find(f"vendor/{licencia}") is not None


@pytest.mark.django_db
def test_las_paginas_apuntan_a_los_archivos_locales(client, crear_usuario):
    from seguridad.models import Rol

    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    pagina = client.get("/agenda/").content.decode()
    for archivo in ("vendor/bootstrap/css/bootstrap.min.css", "vendor/fullcalendar/index.global.min.js"):
        assert f"/static/{archivo}" in pagina
    assert "cdn.jsdelivr" not in pagina
