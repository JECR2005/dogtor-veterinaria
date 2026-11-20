"""S4-16 · Decisión D-21: el cambio incremental deja una base existente protegiendo las ventas.

Simula una base de P4 anterior al cambio, que ya tiene un ticket con un pago, ejecuta
bd/cambios/2026-11-20_RD-06_RD-11_RD-12_ventas.sql dos veces y comprueba que las reglas vuelvan a aplicarse.
Todo ocurre dentro de la transacción de la prueba y se revierte al terminar.
"""

from decimal import Decimal

import pytest
from django.db import DatabaseError, connection, transaction

from bd.ejecutar import CARPETA, ejecutar_scripts
from catalogos.models import CategoriaServicio
from seguridad.models import Rol
from tests import fabricas
from ventas import services
from ventas.models import Pago
from ventas.services import Partida

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CAMBIO = CARPETA / "cambios" / "2026-11-20_RD-06_RD-11_RD-12_ventas.sql"
OBJETOS = {
    "fn_linea_con_receta_valida",
    "CK_detalle_venta_receta_valida",
    "TR_detalle_venta_precio_historico",
    "TR_pago_inmutable",
    "TR_venta_cancelada_solo_lectura",
}
COMO_ANTES = [
    "DROP TRIGGER dbo.TR_detalle_venta_precio_historico",
    "DROP TRIGGER dbo.TR_pago_inmutable",
    "DROP TRIGGER dbo.TR_venta_cancelada_solo_lectura",
    "ALTER TABLE dbo.detalle_venta DROP CONSTRAINT CK_detalle_venta_receta_valida",
    "DROP FUNCTION dbo.fn_linea_con_receta_valida",
]


def _objetos():
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT name FROM sys.objects WHERE name IN ({', '.join(['%s'] * len(OBJETOS))})",
            sorted(OBJETOS),
        )
        return {fila[0] for fila in cursor.fetchall()}


def test_D21_el_cambio_protege_una_base_existente_y_se_puede_repetir(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    venta = services.generar_ticket(
        fabricas.paciente("Max").cliente, recepcion.empleado, [Partida(servicio=bano)]
    )
    pago = services.registrar_pago(venta, recepcion.empleado, "Efectivo", Decimal("500"))

    with connection.cursor() as cursor:
        for sentencia in COMO_ANTES:
            cursor.execute(sentencia)
    assert _objetos() == set()

    ejecutar_scripts(connection, [CAMBIO])
    ejecutar_scripts(connection, [CAMBIO])  # se puede ejecutar más de una vez
    assert _objetos() == OBJETOS
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Pago.objects.filter(pk=pago.pk).update(monto=Decimal("1"))
