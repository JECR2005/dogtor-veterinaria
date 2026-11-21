"""S5-14 · `preparar_carga` deja lo que necesita Locust para TS-06 sin tocar los escenarios de los guiones."""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from clinico.models import Consulta
from inventario.models import Lote
from seguridad.models import AccionBitacora, BitacoraAuditoria
from ventas.services import siguiente_folio

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_S5_14_consultas_abiertas_producto_y_clientes_y_es_repetible(tmp_path):
    salida = tmp_path / "carga.json"
    call_command("cargar_datos_prueba", mascotas=150)
    folio = siguiente_folio()
    call_command("preparar_carga", consultas=3, salida=str(salida))
    call_command("preparar_carga", consultas=3, salida=str(salida))  # repetible: no duplica

    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert len(datos["consultas"]) == 3 and len(datos["clientes"]) == 50 and datos["mascotas"] == 150
    abiertas = Consulta.objects.filter(pk__in=[c["id"] for c in datos["consultas"]])
    assert {c.estado for c in abiertas} == {"Abierta"}
    assert {c.cita.empleado.usuario.nombre_usuario for c in abiertas} == {"veterinario"}
    assert len({c["mascota"] for c in datos["consultas"]}) == 3  # una mascota por usuario de Locust
    assert Lote.objects.get(producto__codigo="CARGA-001").cantidad_disponible == 100_000
    assert datos["producto"].startswith("p-") and datos["servicio"].startswith("s-")
    assert BitacoraAuditoria.objects.filter(entidad="consulta", accion=AccionBitacora.ALTA).count() == 3
    assert siguiente_folio() == folio  # no genera tickets: los escenarios conservan sus folios


def test_S5_14_sin_suficientes_mascotas_lo_dice(tmp_path):
    call_command("cargar_datos_prueba", mascotas=10)
    with pytest.raises(CommandError, match="Faltan mascotas"):
        call_command("preparar_carga", salida=str(tmp_path / "carga.json"))
