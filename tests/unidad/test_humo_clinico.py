"""S0-20 · Prueba de humo del componente `clinico`.

Confirma que la app está instalada y que sus modelos usan exactamente los nombres de tabla del
diccionario de datos (apartado 3.5, Tabla 4.24). Si falla en Sprint 0, el problema es de configuración.
"""

import pytest
from django.apps import apps

pytestmark = pytest.mark.unidad


def test_S0_clinico_instalada_con_tablas_del_diccionario():
    config = apps.get_app_config("clinico")
    tablas = {modelo._meta.db_table for modelo in config.get_models()}
    assert tablas == {
        "aplicacion",
        "consulta",
        "detalle_receta",
        "expediente_clinico",
        "receta",
        "registro_estetica",
    }
