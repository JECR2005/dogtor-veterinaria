"""S5-17 · DEF-008: los identificadores en las plantillas se escriben sin separador de miles.

Con USE_THOUSAND_SEPARATOR = True (es-MX), `{{ cita.pk }}` se escribe «2,309» a partir del registro 1,000, y
una dirección como `?cita=2,309` o un campo oculto con ese valor ya no sirven. TS-10 lo detectó: el botón
Cobrar de «Por cobrar hoy» no llevaba a la cita. Toda salida de un identificador (pk, id, id_…, …_id) y de
un número de página debe pasar por `|unlocalize`.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template

PLANTILLAS = Path(settings.BASE_DIR) / "templates"
VARIABLE = re.compile(r"\{\{\s*([a-z_][a-z_.]*)\s*(\|[^}]*)?\}\}")
NUMEROS_DE_PAGINA = ("previous_page_number", "next_page_number")


def _es_identificador(expresion):
    ultimo = expresion.split(".")[-1]
    if ultimo == "id_for_label":  # texto, no un número
        return False
    return ultimo in ("pk", "id", *NUMEROS_DE_PAGINA) or ultimo.startswith("id_") or ultimo.endswith("_id")


def test_DEF008_ninguna_plantilla_escribe_un_identificador_con_separador_de_miles():
    pendientes = []
    for archivo in sorted(PLANTILLAS.rglob("*.html")):
        texto = archivo.read_text(encoding="utf-8")
        for numero, linea in enumerate(texto.splitlines(), start=1):
            for coincidencia in VARIABLE.finditer(linea):
                expresion, filtros = coincidencia.group(1), coincidencia.group(2) or ""
                if _es_identificador(expresion) and "unlocalize" not in filtros:
                    pendientes.append(f"{archivo.relative_to(PLANTILLAS)}:{numero} {coincidencia.group(0)}")
        if "|unlocalize" in texto:
            assert re.search(r"\{% load [^%]*\bl10n\b", texto), f"{archivo.name}: falta {{% load l10n %}}"
    assert not pendientes, "Use |unlocalize en:\n" + "\n".join(pendientes)


@pytest.mark.parametrize("valor", [7, 2309, 1234567])
def test_DEF008_unlocalize_deja_el_numero_tal_cual(valor):
    plantilla = Template("{% load l10n %}?cita={{ pk|unlocalize }} · {{ pk }}")
    assert plantilla.render(Context({"pk": valor})).startswith(f"?cita={valor} ")
