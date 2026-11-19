"""Servicios (reglas de negocio) del componente «Reportes y documentos».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

- RF-07: PDF de receta (P3).
- RF-13: PDF de ticket y corte de caja (P4).
- RNF-03: exportación de la bitácora (P5).

D-18: los PDF se generan con xhtml2pdf a partir de una plantilla HTML. Este módulo es la única puerta hacia la
biblioteca (R10): si se cambia, solo cambia aquí.
"""

from io import BytesIO

from django.template.loader import render_to_string


class ErrorPDF(Exception):
    """La biblioteca no pudo convertir el HTML en PDF."""


def pdf_desde_html(html):
    """Convierte HTML (con CSS sencillo, tamaño carta) en los bytes de un PDF."""
    from xhtml2pdf import pisa

    salida = BytesIO()
    resultado = pisa.CreatePDF(src=html, dest=salida, encoding="utf-8")
    if resultado.err:
        raise ErrorPDF(f"No se pudo generar el PDF ({resultado.err} errores).")
    return salida.getvalue()


def pdf_desde_plantilla(plantilla, contexto=None):
    """Genera el PDF de una plantilla de Django, por ejemplo «reportes/receta.html»."""
    return pdf_desde_html(render_to_string(plantilla, contexto or {}))
