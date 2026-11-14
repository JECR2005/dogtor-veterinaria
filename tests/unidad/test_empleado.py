"""TU-05 · Empleado (alta): puesto Veterinario sin cédula y con cédula (RF-03, RD-01, Tabla 4.12)."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError

from catalogos.models import Empleado, Puesto

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]


def _empleado(puesto, cedula):
    return Empleado(
        nombre="Laura",
        apellidos="Prueba",
        puesto=puesto,
        cedula_profesional=cedula,
        fecha_ingreso=date.today(),
    )


@pytest.mark.parametrize("cedula", [None, "", "   "])
def test_TU05_veterinario_sin_cedula_no_se_guarda(cedula):
    with pytest.raises(ValidationError) as error:
        _empleado(Puesto.VETERINARIO, cedula).full_clean()
    assert Empleado.MENSAJE_CEDULA in error.value.message_dict["cedula_profesional"]


def test_TU05_veterinario_con_cedula_si_se_guarda():
    empleado = _empleado(Puesto.VETERINARIO, "12345678")
    empleado.full_clean()
    empleado.save()
    assert Empleado.objects.filter(cedula_profesional="12345678").exists()


@pytest.mark.parametrize("puesto", [Puesto.ESTILISTA, Puesto.RECEPCIONISTA, Puesto.ADMINISTRADOR])
def test_los_demas_puestos_no_necesitan_cedula(puesto):
    empleado = _empleado(puesto, "  ")
    empleado.full_clean()
    assert empleado.cedula_profesional is None  # vacío se guarda como NULL (índice filtrado, D-12)
