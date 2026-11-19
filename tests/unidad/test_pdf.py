"""S3-02 · Decisión D-18: los PDF se generan con xhtml2pdf desde una plantilla (RF-07, RF-13)."""

from io import BytesIO

import pytest
from django.template import Context, Template
from pypdf import PdfReader

from reportes import services

pytestmark = pytest.mark.unidad


def test_D18_genera_un_pdf_tamano_carta_desde_html():
    contenido = services.pdf_desde_html(
        "<html><body><h1>Receta R-0001</h1><p>Ñandú, acentos: áéíóú</p></body></html>"
    )
    assert contenido.startswith(b"%PDF-")
    pagina = PdfReader(BytesIO(contenido)).pages[0]
    # Tamaño carta: 8.5 × 11 pulgadas = 612 × 792 puntos
    assert (round(float(pagina.mediabox.width)), round(float(pagina.mediabox.height))) == (612, 792)
    assert "Receta R-0001" in pagina.extract_text()


def test_D18_la_plantilla_base_de_los_documentos_se_convierte():
    html = Template(
        '{% extends "reportes/_base_pdf.html" %}{% block subtitulo %}Prueba{% endblock %}'
        "{% block contenido %}<table><tr><th>Producto</th></tr><tr><td>Amoxicilina</td></tr></table>"
        "{% endblock %}"
    ).render(Context())
    assert services.pdf_desde_html(html).startswith(b"%PDF-")
