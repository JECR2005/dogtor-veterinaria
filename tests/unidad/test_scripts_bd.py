"""Los scripts que ejecuta bd/ejecutar.py abren y cierran cada transacción en el mismo lote.

La conexión del sistema usa MARS, y con MARS SQL Server rechaza una transacción que empieza en un lote (entre
dos GO) y sigue abierta al terminarlo (error 3997). Las pruebas de integración no lo detectan porque corren
dentro de una transacción ya abierta; por eso se revisa el texto de los scripts.
"""

import re

import pytest

from bd.ejecutar import CARPETA, SCRIPT_BORRAR, SCRIPTS_ESQUEMA, lotes_de_script

pytestmark = pytest.mark.unidad

SCRIPTS = [SCRIPT_BORRAR, *SCRIPTS_ESQUEMA, *sorted((CARPETA / "cambios").glob("*.sql"))]
_COMENTARIOS = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
_INICIO = re.compile(r"\bBEGIN\s+TRAN(SACTION)?\b", re.IGNORECASE)
_FIN = re.compile(r"\bCOMMIT\b", re.IGNORECASE)


@pytest.mark.parametrize("ruta", SCRIPTS, ids=lambda ruta: ruta.name)
def test_cada_transaccion_empieza_y_termina_en_el_mismo_lote(ruta):
    for numero, lote in enumerate(lotes_de_script(ruta), start=1):
        codigo = _COMENTARIOS.sub("", lote)
        inicios, fines = len(_INICIO.findall(codigo)), len(_FIN.findall(codigo))
        assert inicios == fines, f"{ruta.name}, lote {numero}: {inicios} BEGIN TRANSACTION y {fines} COMMIT"
