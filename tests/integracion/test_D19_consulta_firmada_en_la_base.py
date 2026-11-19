"""S3-15 · Decisión D-19: el cambio incremental deja una base existente protegiendo la consulta firmada.

Simula una base de P3 anterior al cambio (sin funciones, restricciones ni disparadores de RD-07 y RD-08),
ejecuta bd/cambios/2026-11-19_RD-07_RD-08_consulta_firmada.sql dos veces y comprueba que la regla vuelva a
aplicarse. Todo ocurre dentro de la transacción de la prueba y se revierte al terminar.
"""

from decimal import Decimal

import pytest
from django.db import DatabaseError, connection, transaction

from bd.ejecutar import CARPETA, ejecutar_scripts
from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.models import Consulta
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CAMBIO = CARPETA / "cambios" / "2026-11-19_RD-07_RD-08_consulta_firmada.sql"

OBJETOS = {
    "fn_consulta_abierta",
    "fn_receta_en_consulta_abierta",
    "CK_aplicacion_consulta_abierta",
    "CK_receta_consulta_abierta",
    "CK_detalle_receta_consulta_abierta",
    "TR_consulta_firmada_solo_lectura",
    "TR_consulta_firmada_no_se_borra",
    "TR_aplicacion_de_consulta_firmada",
}

COMO_ANTES = [
    "DROP TRIGGER dbo.TR_consulta_firmada_solo_lectura",
    "DROP TRIGGER dbo.TR_consulta_firmada_no_se_borra",
    "DROP TRIGGER dbo.TR_aplicacion_de_consulta_firmada",
    "ALTER TABLE dbo.aplicacion DROP CONSTRAINT CK_aplicacion_consulta_abierta",
    "ALTER TABLE dbo.receta DROP CONSTRAINT CK_receta_consulta_abierta",
    "ALTER TABLE dbo.detalle_receta DROP CONSTRAINT CK_detalle_receta_consulta_abierta",
    "DROP FUNCTION dbo.fn_receta_en_consulta_abierta",
    "DROP FUNCTION dbo.fn_consulta_abierta",
]


def _objetos():
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT name FROM sys.objects WHERE name IN ({', '.join(['%s'] * len(OBJETOS))})",
            sorted(OBJETOS),
        )
        return {fila[0] for fila in cursor.fetchall()}


def test_D19_el_cambio_protege_una_base_existente_y_se_puede_repetir():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    servicio = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    cita = fabricas.cita_de_hoy(fabricas.paciente("Max"), laura, servicio)
    datos = {"sintomas": "Revisión", "peso_kg": Decimal("28"), "diagnostico": "Sano"}
    consulta = services.firmar(services.abrir_consulta(cita, laura, datos), laura)

    with connection.cursor() as cursor:
        for sentencia in COMO_ANTES:
            cursor.execute(sentencia)
    assert _objetos() == set()

    ejecutar_scripts(connection, [CAMBIO])
    ejecutar_scripts(connection, [CAMBIO])  # se puede ejecutar más de una vez
    assert _objetos() == OBJETOS
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Consulta.objects.filter(pk=consulta.pk).update(diagnostico="Otro")
