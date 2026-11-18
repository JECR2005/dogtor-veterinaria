"""S1-12 · Servicio de agenda: TU-01 a TU-04 (Tabla 4.12) y el procedimiento del apartado 4.3.

TU-01 Agenda.hayEmpalme: cita de 10:00 a 10:30; nueva de 10:15 a 10:45 → «Empalme de horario».
TU-02 Agenda.hayEmpalme (valor límite): nueva de 10:30 a 11:00 → no hay empalme; la cita se guarda.
TU-03 HorarioLaboral.cubre: jornada de 9:00 a 19:00; cita de 18:45 a 19:15 → «Fuera de horario laboral».
TU-04 Empleado.puedePrestar: Estilista y «Consulta general» → falso; la cita no se crea.
"""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from agenda import services
from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, Cliente, EstatusMascota, Mascota, Puesto, Servicio
from tests import fabricas
from tests.fabricas import LUNES, en

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

_empleado = fabricas.empleado
_servicio = fabricas.servicio


@pytest.fixture
def veterinario():
    return _empleado(Puesto.VETERINARIO, cedula="12345678")


@pytest.fixture
def estilista():
    return _empleado(Puesto.ESTILISTA)


@pytest.fixture
def consulta():
    return _servicio("Consulta general", CategoriaServicio.CONSULTA, 30)


@pytest.fixture
def mascota():
    return fabricas.mascota()


# --- TU-01 y TU-02 · Empalmes (RD-02) -------------------------------------------
def test_TU01_hay_empalme_y_aparece_el_mensaje(mascota, veterinario, consulta):
    services.agendar(mascota, veterinario, consulta, en("10:00"))  # 10:00 a 10:30
    assert services.hay_empalme(veterinario, en("10:15"), en("10:45"))
    with pytest.raises(services.CitaRechazada, match="^Empalme de horario$"):
        services.agendar(mascota, veterinario, consulta, en("10:15"))
    assert Cita.objects.count() == 1


def test_TU02_terminar_justo_cuando_otra_inicia_no_es_empalme(mascota, veterinario, consulta):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    assert not services.hay_empalme(veterinario, en("10:30"), en("11:00"))
    cita = services.agendar(mascota, veterinario, consulta, en("10:30"))
    assert cita.estado == EstadoCita.PROGRAMADA
    assert Cita.objects.count() == 2
    # y tampoco antes: de 9:30 a 10:00 queda libre
    assert not services.hay_empalme(veterinario, en("09:30"), en("10:00"))


@pytest.mark.parametrize(
    "inicio, fin",
    [("09:45", "10:15"), ("10:10", "10:20"), ("09:00", "11:00"), ("10:29", "10:59")],
)
def test_todo_traslape_es_empalme(mascota, veterinario, consulta, inicio, fin):
    services.agendar(mascota, veterinario, consulta, en("10:00"))
    assert services.hay_empalme(veterinario, en(inicio), en(fin))


def test_una_cita_cancelada_libera_el_espacio(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    Cita.objects.filter(pk=cita.pk).update(estado=EstadoCita.CANCELADA, motivo_cancelacion="Prueba")
    assert not services.hay_empalme(veterinario, en("10:00"), en("10:30"))


def test_la_cita_que_se_reprograma_no_choca_consigo_misma(mascota, veterinario, consulta):
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    assert not services.hay_empalme(veterinario, en("10:15"), en("10:45"), excluir=cita)


def test_las_citas_de_otro_empleado_no_son_empalme(mascota, veterinario, consulta):
    otro = _empleado(Puesto.VETERINARIO, cedula="87654321")
    services.agendar(fabricas.mascota("Michi", "Bruno"), otro, consulta, en("10:00"))
    assert services.agendar(mascota, veterinario, consulta, en("10:00"))


# --- D-16 · La mascota tampoco puede estar en dos citas a la vez (DEF-001) -----------
def test_D16_la_misma_mascota_no_tiene_dos_citas_a_la_vez_con_otro_empleado(mascota, veterinario, consulta):
    otro = _empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    services.agendar(mascota, veterinario, consulta, en("17:30"))
    with pytest.raises(
        services.CitaRechazada, match="^La mascota ya tiene una cita a esa hora: Consulta general a las 17:30"
    ):
        services.agendar(mascota, otro, consulta, en("17:30"))
    with pytest.raises(services.CitaRechazada, match="La mascota ya tiene una cita a esa hora"):
        services.agendar(mascota, otro, consulta, en("17:45"))  # traslape parcial
    assert Cita.objects.count() == 1


def test_D16_tampoco_con_un_servicio_de_otro_puesto(mascota, veterinario, estilista, consulta):
    bano = _servicio("Baño", CategoriaServicio.ESTETICA, 60)
    services.agendar(mascota, estilista, bano, en("10:00"))  # 10:00 a 11:00
    with pytest.raises(services.CitaRechazada, match="La mascota ya tiene una cita a esa hora: Baño"):
        services.agendar(mascota, veterinario, consulta, en("10:30"))


def test_D16_la_mascota_puede_tener_citas_seguidas_y_una_cancelada_no_cuenta(mascota, veterinario, consulta):
    otro = _empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    assert services.agendar(mascota, otro, consulta, en("10:30"))  # termina justo cuando la otra empieza
    Cita.objects.filter(pk=cita.pk).update(estado=EstadoCita.CANCELADA, motivo_cancelacion="Prueba")
    assert services.agendar(mascota, otro, consulta, en("10:00"))


def test_D16_reprogramar_tampoco_empalma_a_la_mascota(mascota, veterinario, consulta):
    otro = _empleado(Puesto.VETERINARIO, cedula="87654321", nombre="Pedro")
    services.agendar(mascota, otro, consulta, en("12:00"))
    cita = services.agendar(mascota, veterinario, consulta, en("10:00"))
    with pytest.raises(services.CitaRechazada, match="La mascota ya tiene una cita a esa hora"):
        services.reprogramar(cita, en("12:00"))
    services.reprogramar(cita, en("10:15"))  # dentro de su propio espacio sí


# --- TU-03 · Horario laboral (RD-02) ---------------------------------------------
def test_TU03_cita_que_se_sale_de_la_jornada_no_se_cubre(mascota, veterinario, consulta):
    horario = veterinario.horarios.get(dia_semana=1)  # lunes de 9:00 a 19:00
    assert not horario.cubre(en("18:45"), en("19:15"))
    with pytest.raises(services.CitaRechazada, match="^Fuera de horario laboral$"):
        services.agendar(mascota, veterinario, consulta, en("18:45"))
    assert not Cita.objects.exists()


@pytest.mark.parametrize(
    "inicio, cubre", [("09:00", True), ("18:30", True), ("08:45", False), ("18:31", False)]
)
def test_valores_limite_de_la_jornada(veterinario, consulta, inicio, cubre):
    fin = services.calcular_fin(consulta, en(inicio))
    assert services.horario_cubre(veterinario, en(inicio), fin) is cubre


def test_domingo_y_dia_sin_horario_estan_fuera(mascota, veterinario, consulta):
    domingo = LUNES - timedelta(days=1)
    with pytest.raises(services.CitaRechazada, match="Fuera de horario laboral"):
        services.agendar(mascota, veterinario, consulta, en("10:00", domingo))
    veterinario.horarios.filter(dia_semana=2).delete()  # deja de trabajar los martes
    with pytest.raises(services.CitaRechazada, match="Fuera de horario laboral"):
        services.agendar(mascota, veterinario, consulta, en("10:00", LUNES + timedelta(days=1)))


# --- TU-04 · Puesto compatible (RD-04) ------------------------------------------
def test_TU04_el_estilista_no_presta_consulta_general(mascota, estilista, consulta):
    assert estilista.puede_prestar(consulta) is False
    with pytest.raises(services.CitaRechazada, match="lo presta un Veterinario"):
        services.agendar(mascota, estilista, consulta, en("10:00"))
    assert not Cita.objects.exists()


def test_cada_servicio_solo_lo_presta_su_puesto(veterinario, estilista, consulta):
    bano = _servicio("Baño", CategoriaServicio.ESTETICA, 60)
    assert veterinario.puede_prestar(consulta) and not veterinario.puede_prestar(bano)
    assert estilista.puede_prestar(bano) and not estilista.puede_prestar(consulta)
    assert list(services.empleados_para(bano)) == [estilista]  # TI-02: solo estilistas en la lista


def test_un_empleado_inactivo_no_presta_servicios(veterinario, consulta):
    veterinario.activo = False
    assert not veterinario.puede_prestar(consulta)


# --- Paso 1 y paso 5 -------------------------------------------------------------
def test_la_cita_guardada_tiene_la_hora_de_fin_del_servicio(mascota, estilista):
    corte = _servicio("Corte y estética", CategoriaServicio.ESTETICA, 90)
    cita = services.agendar(mascota, estilista, corte, en("11:00"), motivo="  Corte de verano ")
    cita.refresh_from_db()
    assert timezone.localtime(cita.fecha_hora_fin).time() == time(12, 30)
    assert cita.motivo == "Corte de verano"


def test_no_se_agenda_en_el_pasado(mascota, veterinario, consulta):
    ayer = timezone.localdate() - timedelta(days=1)
    with pytest.raises(services.CitaRechazada, match="ya pasó"):
        services.agendar(mascota, veterinario, consulta, en("10:00", ayer))


def test_no_se_agenda_a_clientes_dados_de_baja_ni_mascotas_inactivas(mascota, veterinario, consulta):
    Mascota.objects.filter(pk=mascota.pk).update(estatus=EstatusMascota.FALLECIDA)
    mascota.refresh_from_db()
    with pytest.raises(services.CitaRechazada, match="fallecida"):
        services.agendar(mascota, veterinario, consulta, en("10:00"))
    Cliente.objects.filter(pk=mascota.cliente_id).update(activo=False)
    mascota = Mascota.objects.select_related("cliente").get(pk=mascota.pk)
    with pytest.raises(services.CitaRechazada, match="dado de baja"):
        services.agendar(mascota, veterinario, consulta, en("10:00"))


def test_los_servicios_que_no_se_agendan_se_rechazan(mascota, veterinario):
    aplicacion = _servicio("Aplicación de vacuna", CategoriaServicio.APLICACION, 10)
    Servicio.objects.filter(pk=aplicacion.pk).update(agendable=False)
    aplicacion.refresh_from_db()
    with pytest.raises(services.CitaRechazada, match="no se agenda"):
        services.agendar(mascota, veterinario, aplicacion, en("10:00"))
