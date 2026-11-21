"""TI-08 · Expediente clínico y Agenda (Tabla 4.13): firmar una consulta.

Criterio: la cita pasa a Completada y el peso de la mascota se actualiza (RF-06).
"""

from decimal import Decimal

import pytest

from agenda.models import Cita
from catalogos.models import CategoriaServicio, Mascota, Puesto
from clinico.models import Consulta
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_TI08_firmar_completa_la_cita_y_actualiza_el_peso(client):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    client.force_login(fabricas.cuenta(laura, "laura", rol=Rol.VETERINARIO))
    max_ = fabricas.paciente("Max")
    Mascota.objects.filter(pk=max_.pk).update(peso_actual=Decimal("27.00"))
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )

    datos = {"sintomas": "Revisión", "peso_kg": "28.40", "temperatura_c": "38.6", "diagnostico": "Sano"}
    client.post(f"/clinica/citas/{cita.pk}/atender/", datos)
    consulta = Consulta.objects.get(cita=cita)
    confirmacion = client.get(f"/clinica/consultas/{consulta.pk}/firmar/").content.decode()
    assert "¿Firmar la consulta de Max?" in confirmacion and "28.40 kg" in confirmacion
    assert Cita.objects.get(pk=cita.pk).estado == "Programada"  # ver la confirmación no firma (RI-04)

    respuesta = client.post(f"/clinica/consultas/{consulta.pk}/firmar/", follow=True)
    assert "Consulta firmada. La cita quedó completada" in respuesta.content.decode()
    assert Cita.objects.get(pk=cita.pk).estado == "Completada"
    assert Mascota.objects.get(pk=max_.pk).peso_actual == Decimal("28.40")
    assert Consulta.objects.get(pk=consulta.pk).estado == "Firmada"
