"""S5-04 · Decisión D-23: el cambio incremental deja una base existente con la bitácora inmutable.

Simula una base de P4 anterior al cambio, que ya tiene registros en la bitácora, ejecuta
bd/cambios/2026-11-21_RNF-03_bitacora_inmutable.sql dos veces y comprueba que la regla vuelva a aplicarse.
Todo ocurre dentro de la transacción de la prueba y se revierte al terminar.
"""

import pytest
from django.db import DatabaseError, connection, transaction

from bd.ejecutar import CARPETA, ejecutar_scripts
from catalogos import services as catalogos
from seguridad.models import BitacoraAuditoria, Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CAMBIO = CARPETA / "cambios" / "2026-11-21_RNF-03_bitacora_inmutable.sql"
COMO_ANTES = [
    "DROP TRIGGER dbo.TR_bitacora_inmutable",
    "DROP INDEX IX_bitacora_usuario_fecha ON dbo.bitacora_auditoria",
]


def _objetos():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT (SELECT COUNT(*) FROM sys.triggers WHERE name = 'TR_bitacora_inmutable'), "
            "(SELECT COUNT(*) FROM sys.indexes WHERE name = 'IX_bitacora_usuario_fecha')"
        )
        return tuple(cursor.fetchone())


def test_D23_el_cambio_protege_la_bitacora_de_una_base_existente_y_se_puede_repetir(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    catalogos.dar_de_baja_cliente(fabricas.mascota().cliente, recepcion)
    registro = BitacoraAuditoria.objects.get()

    with connection.cursor() as cursor:
        for sentencia in COMO_ANTES:
            cursor.execute(sentencia)
    assert _objetos() == (0, 0)

    ejecutar_scripts(connection, [CAMBIO])
    ejecutar_scripts(connection, [CAMBIO])  # se puede ejecutar más de una vez
    assert _objetos() == (1, 1)
    with pytest.raises(DatabaseError, match="RNF-03"), transaction.atomic():
        BitacoraAuditoria.objects.filter(pk=registro.pk).update(entidad="otra")
    assert BitacoraAuditoria.objects.get().entidad == "cliente"
