"""Configuración común de pytest.

Las 26 tablas no las crean las migraciones de Django (managed = False, decisión D-10): después de que
pytest-django crea la base de pruebas test_Dogtor, aquí se ejecutan los mismos scripts T-SQL que se usan
en producción (bd/01_tablas.sql y bd/02_vistas.sql). Así las pruebas verifican el esquema real,
con sus restricciones, índices, vista y disparador.

Nota: no usen `@pytest.mark.django_db(transaction=True)`; Django no vacía las tablas no administradas
entre pruebas. Las pruebas normales se revierten al terminar, que es lo que se necesita.
"""

import pytest

from bd.ejecutar import SCRIPTS_ESQUEMA, ejecutar_scripts


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    from django.db import connection

    with django_db_blocker.unblock():
        ejecutar_scripts(connection, SCRIPTS_ESQUEMA)
