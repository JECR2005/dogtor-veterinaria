"""TU-17 · Recordatorios (Tabla 4.12): la lista del día sale de las próximas dosis y de las citas de mañana.

Criterio: una dosis que vence en 3 días aparece en la lista de hoy; una a 4 días todavía no. La cita
programada de mañana también aparece; la cancelada no. Generar dos veces no repite recordatorios (RF-09).
"""

from datetime import date, timedelta

import pytest
from django.utils import timezone

from catalogos.models import CategoriaProducto, CategoriaServicio, PreferenciaContacto, Puesto
from recordatorios import services
from recordatorios.models import EstadoRecordatorio, Recordatorio, TipoRecordatorio
from tests import fabricas

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def laura():
    return fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")


@pytest.fixture
def vacuna():
    return fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)


def test_TU17_la_dosis_a_3_dias_aparece_y_la_de_4_todavia_no(laura, vacuna):
    a_tres = fabricas.aplicacion(fabricas.paciente("Michi"), laura, vacuna, 3, hora="09:00")
    fabricas.aplicacion(fabricas.paciente("Rocky"), laura, vacuna, 4, hora="10:00")

    assert services.generar(HOY) == 1
    recordatorio = Recordatorio.objects.get()
    assert recordatorio.aplicacion == a_tres
    assert recordatorio.tipo == TipoRecordatorio.PROXIMA_DOSIS
    assert recordatorio.fecha_objetivo == HOY + timedelta(days=3)
    assert recordatorio.estado == EstadoRecordatorio.PENDIENTE

    # Al día siguiente la de Rocky ya entra en las 72 horas
    assert services.generar(HOY + timedelta(days=1)) == 1


def test_TU17_la_cita_de_manana_aparece_y_la_cancelada_no(laura):
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    manana = HOY + timedelta(days=1)
    cita = fabricas.cita_de_hoy(fabricas.mascota("Canela"), laura, consulta, "11:00", dia=manana)
    fabricas.cita_de_hoy(fabricas.mascota("Toby"), laura, consulta, "12:00", dia=manana, estado="Cancelada")
    fabricas.cita_de_hoy(fabricas.mascota("Luna"), laura, consulta, "13:00")  # hoy: no se avisa

    services.generar(HOY)
    recordatorio = Recordatorio.objects.get()
    assert recordatorio.cita == cita and recordatorio.tipo == TipoRecordatorio.CITA
    assert recordatorio.fecha_objetivo == manana


def test_TU17_generar_dos_veces_no_repite(laura, vacuna):
    fabricas.aplicacion(fabricas.paciente("Michi"), laura, vacuna, 2)
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    fabricas.cita_de_hoy(fabricas.mascota("Canela"), laura, consulta, "11:00", dia=HOY + timedelta(days=1))

    assert services.generar(HOY) == 2
    assert services.generar(HOY) == 0
    assert Recordatorio.objects.count() == 2


def test_TU17_desparasitante_tambien_y_otros_productos_no(laura):
    desparasitante = fabricas.producto(
        "DES-001", "Desparasitante", stock_minimo=0, categoria=CategoriaProducto.DESPARASITANTE
    )
    fabricas.aplicacion(fabricas.paciente("Rocky"), laura, desparasitante, 1)
    services.generar(HOY)
    assert Recordatorio.objects.get().tipo == TipoRecordatorio.PROXIMA_DOSIS


def test_TU17_una_dosis_posterior_ya_cubre_la_anterior(laura, vacuna):
    """Si después se aplicó otra vez el mismo producto, el aviso de la dosis vieja ya no hace falta."""
    michi = fabricas.paciente("Michi")
    fabricas.aplicacion(michi, laura, vacuna, 2, hora="09:00")
    fabricas.aplicacion(michi, laura, vacuna, 300, hora="10:00")
    assert services.generar(HOY) == 0


@pytest.mark.parametrize(
    "hoy, dias",
    [
        (date(2026, 11, 18), [date(2026, 11, 19)]),  # miércoles: avisa las del jueves
        (date(2026, 11, 21), [date(2026, 11, 22), date(2026, 11, 23)]),  # sábado: domingo y lunes
    ],
)
def test_TU17_el_sabado_tambien_se_avisan_las_citas_del_lunes(hoy, dias):
    assert services.dias_de_citas_a_avisar(hoy) == dias


@pytest.mark.parametrize(
    "preferencia, correo, inicio",
    [
        (PreferenciaContacto.WHATSAPP, None, "https://wa.me/528331234567?text=Hola%20Ana"),
        (PreferenciaContacto.CORREO, "ana@ejemplo.com", "mailto:ana@ejemplo.com?subject="),
        (PreferenciaContacto.TELEFONO, None, "tel:+528331234567"),
        (PreferenciaContacto.CORREO, None, "tel:+528331234567"),  # sin correo capturado, se llama
    ],
)
def test_el_enlace_abre_el_canal_preferido(laura, vacuna, preferencia, correo, inicio):
    michi = fabricas.paciente("Michi")
    michi.cliente.preferencia_contacto = preferencia
    michi.cliente.correo = correo
    michi.cliente.save()
    fabricas.aplicacion(michi, laura, vacuna, 3)
    services.generar(HOY)

    (recordatorio,) = services.lista_del_dia(HOY)["pendientes"]
    assert recordatorio.enlace.startswith(inicio)
    assert recordatorio.motivo == "Próxima dosis: Vacuna antirrábica"
    assert recordatorio.cuando == "en 3 días"
    assert "Michi" in recordatorio.mensaje and f"{HOY + timedelta(days=3):%d/%m/%Y}" in recordatorio.mensaje


def test_registrar_resultado_guarda_quien_y_cuando_y_no_se_repite(laura, vacuna):
    fabricas.aplicacion(fabricas.paciente("Michi"), laura, vacuna, 3)
    services.generar(HOY)
    recordatorio = Recordatorio.objects.get()
    recepcion = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Rosa")

    services.registrar_resultado(recordatorio, recepcion, EstadoRecordatorio.SIN_RESPUESTA)
    lista = services.lista_del_dia(HOY)
    assert lista["pendientes"] == [] and len(lista["sin_respuesta"]) == 1
    assert services.pendientes(HOY).count() == 0

    hecho = services.registrar_resultado(recordatorio, recepcion, EstadoRecordatorio.CONTACTADO)
    assert hecho.estado == EstadoRecordatorio.CONTACTADO and hecho.empleado == recepcion
    primera = hecho.fecha_contacto
    otra_vez = services.registrar_resultado(recordatorio, laura, EstadoRecordatorio.SIN_RESPUESTA)
    assert otra_vez.estado == EstadoRecordatorio.CONTACTADO and otra_vez.fecha_contacto == primera
    assert len(services.lista_del_dia(HOY)["contactados"]) == 1

    with pytest.raises(ValueError):
        services.registrar_resultado(recordatorio, recepcion, EstadoRecordatorio.PENDIENTE)
