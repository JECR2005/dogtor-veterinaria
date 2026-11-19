"""S3-05 · Consulta clínica: firma con cédula (RD-01) y solo lectura después de firmar (RD-07, TU-14).

TU-14 Consulta (firma): el veterinario intenta editar el diagnóstico de una consulta firmada → se rechaza; el
campo es de solo lectura.
"""

from decimal import Decimal

import pytest
from django.utils import timezone

from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.models import Consulta, ConsultaFirmada, EstadoConsulta
from tests import fabricas

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

DATOS = {
    "sintomas": "Tos seca",
    "peso_kg": Decimal("28.50"),
    "temperatura_c": Decimal("38.9"),
    "diagnostico": None,
}


@pytest.fixture
def escenario():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    consulta_general = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    max_ = fabricas.paciente("Max", alergias="Penicilina")
    cita = fabricas.cita_de_hoy(max_, laura, consulta_general)
    return laura, cita, max_


def _firmada(laura, cita):
    consulta = services.abrir_consulta(cita, laura, {**DATOS, "diagnostico": "Traqueobronquitis"})
    return services.firmar(consulta, laura)


def test_S3_05_abrir_y_firmar_deja_la_consulta_firmada_con_autor_y_fecha(escenario):
    laura, cita, _ = escenario
    consulta = _firmada(laura, cita)
    assert (consulta.estado, consulta.empleado) == (EstadoConsulta.FIRMADA, laura)
    assert consulta.fecha_firma is not None and consulta.fecha_firma <= timezone.now()


def test_TU14_el_diagnostico_de_una_consulta_firmada_no_se_puede_editar(escenario):
    laura, cita, _ = escenario
    consulta = _firmada(laura, cita)
    with pytest.raises(ConsultaFirmada, match="solo lectura"):
        services.guardar_consulta(consulta, laura, {**DATOS, "diagnostico": "Otro diagnóstico"})
    consulta.diagnostico = "Cambio directo en el modelo"
    with pytest.raises(ConsultaFirmada):  # RD-07: también el modelo la rechaza
        consulta.save()
    assert Consulta.objects.get(pk=consulta.pk).diagnostico == "Traqueobronquitis"


def test_TU14_tampoco_se_vuelve_a_firmar(escenario):
    laura, cita, _ = escenario
    consulta = _firmada(laura, cita)
    with pytest.raises(ConsultaFirmada):
        services.firmar(consulta, laura)


@pytest.mark.parametrize("puesto", [Puesto.ESTILISTA, Puesto.ADMINISTRADOR, Puesto.RECEPCIONISTA])
def test_S3_05_RD01_solo_un_veterinario_con_cedula_firma(escenario, puesto):
    laura, cita, _ = escenario
    consulta = services.abrir_consulta(cita, laura, {**DATOS, "diagnostico": "Sano"})
    otro = fabricas.empleado(puesto, nombre=f"Otro {puesto}")
    with pytest.raises(services.ErrorClinico, match="cédula profesional"):
        services.firmar(consulta, otro)
    assert Consulta.objects.get(pk=consulta.pk).estado == EstadoConsulta.ABIERTA


def test_S3_05_otro_veterinario_no_firma_ni_captura_la_consulta_ajena(escenario):
    laura, cita, _ = escenario
    consulta = services.abrir_consulta(cita, laura, {**DATOS, "diagnostico": "Sano"})
    pedro = fabricas.empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    with pytest.raises(services.ErrorClinico, match="veterinario asignado"):
        services.firmar(consulta, pedro)
    with pytest.raises(services.ErrorClinico, match="veterinario asignado"):
        services.guardar_consulta(consulta, pedro, DATOS)


def test_S3_05_sin_diagnostico_no_se_firma(escenario):
    laura, cita, _ = escenario
    consulta = services.abrir_consulta(cita, laura, DATOS)
    with pytest.raises(services.ErrorClinico, match="capture: diagnóstico"):
        services.firmar(consulta, laura)


def test_S3_04_una_cita_solo_tiene_una_consulta_y_debe_estar_programada(escenario):
    laura, cita, max_ = escenario
    services.abrir_consulta(cita, laura, DATOS)
    with pytest.raises(services.ErrorClinico, match="ya tiene su consulta"):
        services.abrir_consulta(cita, laura, DATOS)
    cancelada = fabricas.cita_de_hoy(max_, laura, cita.servicio, hora="12:00", estado="Cancelada")
    with pytest.raises(services.ErrorClinico, match="cancelada"):
        services.abrir_consulta(cancelada, laura, DATOS)


def test_S3_04_la_estetica_no_se_atiende_como_consulta(escenario):
    laura, _, max_ = escenario
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    estilista = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    cita = fabricas.cita_de_hoy(max_, estilista, bano, hora="12:00")
    assert not services.puede_atender(laura, cita) and not services.puede_atender(estilista, cita)
