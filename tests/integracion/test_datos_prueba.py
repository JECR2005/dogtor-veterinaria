"""S0-19 · El comando de datos ficticios es repetible y respeta las reglas del modelo."""

import pytest
from django.core.management import call_command

from catalogos.models import Especie, Mascota
from clinico.models import ExpedienteClinico
from inventario.models import Lote, MovimientoInventario
from seguridad.models import Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_S0_carga_los_datos_y_es_idempotente():
    call_command("cargar_datos_prueba", mascotas=20)
    call_command("cargar_datos_prueba", mascotas=20)  # la segunda vez no duplica nada

    assert Especie.objects.count() == 2
    assert Mascota.objects.count() == 20
    assert ExpedienteClinico.objects.count() == 20  # RD-10: un expediente por mascota
    assert set(Usuario.objects.values_list("rol", flat=True)) == {
        "Administrador",
        "Veterinario",
        "Estilista",
        "Recepcionista",
    }
    # Cada lote tiene su movimiento de entrada (trazabilidad del inventario)
    assert MovimientoInventario.objects.count() == Lote.objects.count()


def test_S0_amplia_hasta_la_cantidad_pedida():
    call_command("cargar_datos_prueba", mascotas=10)
    call_command("cargar_datos_prueba", mascotas=25)
    assert Mascota.objects.count() == 25
