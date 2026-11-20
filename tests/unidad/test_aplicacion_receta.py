"""S3-07 y S3-08 · Aplicaciones y recetas dentro de la consulta (Tabla 4.12): TU-15 y TU-16.

TU-15 Receta: sin consulta abierta se rechaza; con ella hay folio y las existencias no cambian (RD-08).
TU-16 Aplicación: una vacuna sin próxima fecha se rechaza; la próxima fecha es obligatoria (RF-08).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.models import Aplicacion, ConsultaFirmada, Receta
from inventario.models import Lote, MovimientoInventario
from tests import fabricas

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

HOY = timezone.localdate()
EN_UN_ANIO = HOY + timedelta(days=365)


@pytest.fixture
def consulta():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    cita = fabricas.cita_de_hoy(
        fabricas.paciente("Max"), laura, fabricas.servicio("Vacunación", CategoriaServicio.VACUNACION, 20)
    )
    return services.abrir_consulta(cita, laura, {"sintomas": "Vacunación anual", "peso_kg": Decimal("28")})


@pytest.fixture
def vacuna():
    producto = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    tarde = fabricas.lote(producto, 10, 300, numero="TARDE")
    pronto = fabricas.lote(producto, 2, 40, numero="PRONTO")
    return producto, pronto, tarde


def _existencias(*lotes):
    return [Lote.objects.get(pk=lote.pk).cantidad_disponible for lote in lotes]


# --- TU-16 y S3-07 ---------------------------------------------------------------------
def test_TU16_una_vacuna_sin_proxima_fecha_se_rechaza(consulta, vacuna):
    producto, pronto, tarde = vacuna
    with pytest.raises(services.ErrorClinico, match="la próxima fecha es obligatoria"):
        services.registrar_aplicacion(consulta, consulta.empleado, producto, 1, "1 mL subcutánea", None)
    assert not Aplicacion.objects.exists() and _existencias(pronto, tarde) == [Decimal("2"), Decimal("10")]


def test_TU16_la_base_tambien_exige_la_proxima_fecha_en_vacunas(consulta, vacuna):
    _, pronto, _ = vacuna
    with pytest.raises(IntegrityError, match="CK_aplicacion_proxima_fecha"), transaction.atomic():
        Aplicacion.objects.create(consulta=consulta, lote=pronto, tipo="Vacuna", cantidad=1, dosis="1 mL")


def test_S3_07_la_aplicacion_descuenta_una_sola_vez_el_lote_que_caduca_primero(consulta, vacuna):
    producto, pronto, tarde = vacuna
    (aplicacion,) = services.registrar_aplicacion(
        consulta, consulta.empleado, producto, 1, "1 mL SC", EN_UN_ANIO
    )
    assert (aplicacion.lote, aplicacion.tipo, aplicacion.proxima_fecha) == (pronto, "Vacuna", EN_UN_ANIO)
    assert _existencias(pronto, tarde) == [Decimal("1"), Decimal("10")]
    movimiento = MovimientoInventario.objects.get()
    assert (movimiento.tipo, movimiento.cantidad, movimiento.referencia) == (
        "Aplicación",
        Decimal("-1"),
        f"Consulta {consulta.pk}",
    )


def test_S3_07_si_toma_de_dos_lotes_queda_una_aplicacion_por_lote(consulta, vacuna):
    producto, pronto, tarde = vacuna
    aplicadas = services.registrar_aplicacion(consulta, consulta.empleado, producto, 3, "3 dosis", EN_UN_ANIO)
    assert [(a.lote.numero_lote, a.cantidad) for a in aplicadas] == [
        ("PRONTO", Decimal("2")),
        ("TARDE", Decimal("1")),
    ]
    assert _existencias(pronto, tarde) == [Decimal("0"), Decimal("9")]


def test_S3_07_sin_stock_suficiente_no_se_registra_nada(consulta, vacuna):
    producto, pronto, tarde = vacuna
    with pytest.raises(services.ErrorClinico, match="Stock insuficiente"):
        services.registrar_aplicacion(consulta, consulta.empleado, producto, 13, "13 dosis", EN_UN_ANIO)
    assert not Aplicacion.objects.exists() and _existencias(pronto, tarde) == [Decimal("2"), Decimal("10")]


def test_S3_07_un_medicamento_se_aplica_sin_proxima_fecha_y_con_decimales(consulta):
    ivermectina = fabricas.producto("MED-003", "Ivermectina", categoria="Medicamento", unidad_medida="mL")
    lote = fabricas.lote(ivermectina, "10.00")
    (aplicacion,) = services.registrar_aplicacion(
        consulta, consulta.empleado, ivermectina, "0.5", "0.5 mL SC"
    )
    assert (aplicacion.tipo, aplicacion.proxima_fecha) == ("Otro", None)
    assert _existencias(lote) == [Decimal("9.50")]


def test_S3_07_quitar_una_aplicacion_devuelve_al_lote_con_un_movimiento(consulta, vacuna):
    producto, pronto, _ = vacuna
    (aplicacion,) = services.registrar_aplicacion(
        consulta, consulta.empleado, producto, 1, "1 mL", EN_UN_ANIO
    )
    services.quitar_aplicacion(aplicacion, consulta.empleado)
    assert not Aplicacion.objects.exists() and _existencias(pronto) == [Decimal("2")]
    assert sorted(MovimientoInventario.objects.values_list("tipo", "cantidad")) == [
        ("Aplicación", Decimal("-1")),
        ("Devolución", Decimal("1")),
    ]


def test_S3_07_con_la_consulta_firmada_ya_no_se_aplica_ni_se_quita(consulta, vacuna):
    producto, _, _ = vacuna
    (aplicacion,) = services.registrar_aplicacion(
        consulta, consulta.empleado, producto, 1, "1 mL", EN_UN_ANIO
    )
    services.guardar_consulta(
        consulta, consulta.empleado, {"sintomas": "x", "peso_kg": 28, "diagnostico": "Sano"}
    )
    services.firmar(consulta, consulta.empleado)
    with pytest.raises(ConsultaFirmada):
        services.registrar_aplicacion(consulta, consulta.empleado, producto, 1, "1 mL", EN_UN_ANIO)
    with pytest.raises(ConsultaFirmada):
        services.quitar_aplicacion(aplicacion, consulta.empleado)


# --- TU-15 y S3-08 ---------------------------------------------------------------------
def _partidas(producto):
    return [(producto, "1 tableta", "Cada 12 horas", 7, "Con alimento")]


def test_TU15_sin_consulta_abierta_no_hay_receta_y_con_ella_hay_folio_sin_mover_existencias(consulta, vacuna):
    amoxicilina = fabricas.producto("MED-001", "Amoxicilina", categoria="Medicamento", requiere_receta=True)
    lote = fabricas.lote(amoxicilina, 30)
    with pytest.raises(services.ErrorClinico, match="dentro de una consulta abierta"):
        services.emitir_receta(None, consulta.empleado, _partidas(amoxicilina))
    receta = services.emitir_receta(consulta, consulta.empleado, _partidas(amoxicilina), "Reposo")
    assert receta.folio == f"R-{HOY:%Y}-00001"
    assert receta.detalles.get().frecuencia == "Cada 12 horas"
    assert _existencias(lote) == [Decimal("30")] and not MovimientoInventario.objects.exists()


def test_TU15_con_la_consulta_firmada_ya_no_se_emite_receta(consulta):
    amoxicilina = fabricas.producto("MED-001", "Amoxicilina", categoria="Medicamento")
    services.guardar_consulta(
        consulta, consulta.empleado, {"sintomas": "x", "peso_kg": 28, "diagnostico": "Sano"}
    )
    services.firmar(consulta, consulta.empleado)
    with pytest.raises(ConsultaFirmada):
        services.emitir_receta(consulta, consulta.empleado, _partidas(amoxicilina))
    assert not Receta.objects.exists()


def test_S3_08_los_folios_son_consecutivos_y_solo_receta_un_veterinario(consulta):
    amoxicilina = fabricas.producto("MED-001", "Amoxicilina", categoria="Medicamento")
    meloxicam = fabricas.producto("MED-002", "Meloxicam", categoria="Medicamento")
    primera = services.emitir_receta(consulta, consulta.empleado, _partidas(amoxicilina))
    segunda = services.emitir_receta(consulta, consulta.empleado, _partidas(meloxicam))
    assert (primera.folio, segunda.folio) == (f"R-{HOY:%Y}-00001", f"R-{HOY:%Y}-00002")
    estilista = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    with pytest.raises(services.ErrorClinico, match="cédula"):
        services.emitir_receta(consulta, estilista, _partidas(amoxicilina))
    with pytest.raises(services.ErrorClinico, match="dos veces"):
        services.emitir_receta(consulta, consulta.empleado, _partidas(amoxicilina) * 2)
