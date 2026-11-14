"""S1-11 · Servicio: la duración define la hora de fin y el puesto sale de la categoría (RF-04, RD-04)."""

from datetime import datetime
from decimal import Decimal

import pytest

from catalogos.models import CategoriaServicio, PuestoRequerido, Servicio
from catalogos.templatetags.formato import duracion, pesos

pytestmark = pytest.mark.unidad


def _servicio(categoria=CategoriaServicio.CONSULTA, duracion_min=30, agendable=True):
    return Servicio(
        nombre="Prueba",
        categoria=categoria,
        precio=Decimal("400"),
        duracion_min=duracion_min,
        agendable=agendable,
    )


@pytest.mark.parametrize(
    "inicio, minutos, fin",
    [("10:00", 30, "10:30"), ("18:30", 30, "19:00"), ("09:15", 90, "10:45"), ("11:50", 20, "12:10")],
)
def test_S1_11_la_duracion_define_la_hora_de_fin(inicio, minutos, fin):
    dia = "2026-11-16 "
    servicio = _servicio(duracion_min=minutos)
    assert servicio.calcular_fin(datetime.fromisoformat(dia + inicio)) == datetime.fromisoformat(dia + fin)


@pytest.mark.parametrize(
    "categoria, puesto",
    [
        (CategoriaServicio.ESTETICA, PuestoRequerido.ESTILISTA),
        (CategoriaServicio.CONSULTA, PuestoRequerido.VETERINARIO),
        (CategoriaServicio.VACUNACION, PuestoRequerido.VETERINARIO),
        (CategoriaServicio.APLICACION, PuestoRequerido.VETERINARIO),
    ],
)
def test_RD04_el_puesto_se_deduce_de_la_categoria(categoria, puesto):
    servicio = _servicio(categoria=categoria)
    servicio.puesto_requerido = None
    servicio.clean()
    assert servicio.puesto_requerido == puesto


def test_las_aplicaciones_no_se_agendan():
    servicio = _servicio(categoria=CategoriaServicio.APLICACION, agendable=True)
    servicio.clean()
    assert servicio.agendable is False


@pytest.mark.parametrize(
    "valor, texto",
    [
        (Decimal("1250"), "$1,250.00"),
        (Decimal("350.5"), "$350.50"),
        (0, "$0.00"),
        (None, "—"),
        ("12345.678", "$12,345.68"),
    ],
)
def test_RI13_importes_en_pesos_con_separador_de_miles(valor, texto):
    assert pesos(valor) == texto


@pytest.mark.parametrize("minutos, texto", [(45, "45 min"), (60, "1 h"), (90, "1 h 30 min"), (None, "—")])
def test_duracion_legible(minutos, texto):
    assert duracion(minutos) == texto
