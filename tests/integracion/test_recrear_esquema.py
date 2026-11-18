"""`bd/ejecutar.py --recrear` borra todo aunque Django haya guardado historial de /admin-local/.

Antes, 99_borrar_tablas.sql se detenía en `usuario` porque django_admin_log la referencia (error 3726)
y dejaba la base a medio borrar. Todo ocurre dentro de la transacción de la prueba y se revierte al terminar.
"""

import pytest
from django.contrib.admin.models import ADDITION, LogEntry
from django.db import connection

from bd.ejecutar import SCRIPT_BORRAR, SCRIPTS_ESQUEMA, ejecutar_scripts
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def _tablas():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sys.tables")
        return {fila[0] for fila in cursor.fetchall()}


def test_recrear_borra_aunque_haya_historial_de_admin_local(crear_usuario):
    usuario = crear_usuario("administrador", rol=Rol.ADMINISTRADOR)
    LogEntry.objects.create(
        user=usuario, action_flag=ADDITION, object_repr="Lote de prueba", change_message=""
    )

    ejecutar_scripts(connection, [SCRIPT_BORRAR])
    tablas = _tablas()
    assert "usuario" not in tablas and "lote" not in tablas
    assert not {t for t in tablas if t.startswith(("django_", "auth_"))}  # migrate las vuelve a crear

    ejecutar_scripts(connection, SCRIPTS_ESQUEMA)
    tablas = _tablas()
    assert {"usuario", "lote", "movimiento_inventario", "cita"} <= tablas
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM dbo.usuario")
        assert cursor.fetchone()[0] == 0
