"""S3-12 y S3-13 · Reglas de la atención de estética (RF-10, RD-04).

La atención la registra el estilista asignado, el día de la cita, una sola vez, y completa la cita. Para
avisar al veterinario hay que describir el hallazgo; el aviso sigue pendiente hasta que la mascota pasa a
consulta.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from agenda.models import EstadoCita
from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.forms import RegistroEsteticaForm
from clinico.models import RegistroEstetica
from tests import fabricas

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

HOY = timezone.localdate()
DATOS = {
    "estado_pelaje_piel": "Pelaje opaco, piel enrojecida en el lomo",
    "hallazgos": "",
    "observaciones": "",
}


@pytest.fixture
def escenario():
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    canela = fabricas.paciente("Canela")
    cita = fabricas.cita_de_hoy(canela, mario, bano, "12:00")
    return mario, laura, bano, canela, cita


def test_el_registro_completa_la_cita(escenario):
    mario, _, _, canela, cita = escenario
    registro = services.registrar_estetica(cita, mario, DATOS)
    cita.refresh_from_db()
    assert cita.estado == EstadoCita.COMPLETADA
    assert registro.cita == cita and registro.aviso_veterinario is False and registro.hallazgos is None
    assert [e["tipo"] for e in services.historial(canela)] == ["estetica"]  # RF-10: queda en el historial


def test_solo_el_estilista_asignado_y_una_sola_vez(escenario):
    mario, laura, _, _, cita = escenario
    otro = fabricas.empleado(Puesto.ESTILISTA, nombre="Sofía")
    for empleado in (otro, laura, None):
        with pytest.raises(services.ErrorClinico, match="estilista asignado"):
            services.registrar_estetica(cita, empleado, DATOS)
    services.registrar_estetica(cita, mario, DATOS)
    with pytest.raises(services.ErrorClinico, match="ya está completada"):
        services.registrar_estetica(cita, mario, DATOS)
    assert RegistroEstetica.objects.count() == 1


def test_no_se_registra_antes_del_dia_de_la_cita(escenario):
    mario, _, bano, canela, _ = escenario
    manana = fabricas.cita_de_hoy(canela, mario, bano, "10:00", dia=HOY + timedelta(days=1))
    with pytest.raises(services.ErrorClinico, match="el día de la cita"):
        services.registrar_estetica(manana, mario, DATOS)


def test_la_cita_cancelada_no_se_registra(escenario):
    mario, _, bano, canela, _ = escenario
    cancelada = fabricas.cita_de_hoy(canela, mario, bano, "15:00", estado="Cancelada")
    with pytest.raises(services.ErrorClinico, match="ya está cancelada"):
        services.registrar_estetica(cancelada, mario, DATOS)


def test_para_avisar_hay_que_describir_el_hallazgo(escenario):
    mario, _, _, _, cita = escenario
    with pytest.raises(services.ErrorClinico, match="describa el hallazgo"):
        services.registrar_estetica(cita, mario, {**DATOS, "aviso_veterinario": True, "hallazgos": "  "})
    formulario = RegistroEsteticaForm({**DATOS, "aviso_veterinario": "on"})
    assert not formulario.is_valid()
    assert formulario.errors["hallazgos"] == ["Para avisar al veterinario, describa el hallazgo."]
    assert RegistroEsteticaForm({"hallazgos": "x"}).errors["estado_pelaje_piel"]  # obligatorio


def test_la_agenda_de_estetica_solo_trae_citas_de_estetica(escenario):
    mario, laura, _, canela, cita = escenario
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    fabricas.cita_de_hoy(canela, laura, consulta, "09:00")
    otra = fabricas.empleado(Puesto.ESTILISTA, nombre="Sofía")
    fabricas.cita_de_hoy(fabricas.paciente("Toby"), otra, cita.servicio, "13:00")
    fabricas.cita_de_hoy(fabricas.paciente("Luna"), mario, cita.servicio, "17:00", estado="Cancelada")

    assert [c.mascota.nombre for c in services.citas_de_estetica_del_dia(HOY)] == ["Canela", "Toby"]
    (propia,) = services.citas_de_estetica_del_dia(HOY, mario)
    assert propia == cita and propia.registro is None
    services.registrar_estetica(cita, mario, DATOS)
    assert services.citas_de_estetica_del_dia(HOY, mario)[0].registro is not None


def test_el_aviso_sigue_pendiente_hasta_que_la_mascota_pasa_a_consulta(escenario):
    mario, laura, _, canela, cita = escenario
    aviso = services.registrar_estetica(
        cita, mario, {**DATOS, "hallazgos": "Garrapatas detrás de las orejas", "aviso_veterinario": True}
    )
    assert services.avisos_pendientes() == [aviso]
    assert services.avisos_de_la_mascota(canela) == [aviso]
    assert services.avisos_de_la_mascota(fabricas.paciente("Toby")) == []

    revision = fabricas.cita_de_hoy(
        canela, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30), "18:00"
    )
    services.abrir_consulta(revision, laura, {"sintomas": "Revisión por aviso", "peso_kg": Decimal("12")})
    assert services.avisos_pendientes() == []
    assert services.avisos_de_la_mascota(canela) == [aviso]  # se sigue mostrando en esa consulta


def test_sin_aviso_o_de_hace_mas_de_un_mes_no_aparece(escenario):
    mario, _, bano, canela, cita = escenario
    services.registrar_estetica(cita, mario, {**DATOS, "hallazgos": "Uñas largas"})  # sin aviso
    viejo = fabricas.cita_de_hoy(canela, mario, bano, "10:00", dia=HOY - timedelta(days=40))
    services.registrar_estetica(
        viejo,
        mario,
        {**DATOS, "hallazgos": "Bulto en el costado", "aviso_veterinario": True},
        ahora=timezone.now() - timedelta(days=40),
    )
    assert services.avisos_pendientes() == []
