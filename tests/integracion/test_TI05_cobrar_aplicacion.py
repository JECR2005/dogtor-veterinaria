"""TI-05 · Expediente clínico, Ventas e Inventario (Tabla 4.13): cobrar la vacuna aplicada con el servicio
del catálogo. Criterio: el lote no baja por segunda vez (RD-09, R08). D-20: «Aplicación de vacuna»."""

from decimal import Decimal

import pytest

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaServicio, Puesto
from inventario.models import Lote, MovimientoInventario
from seguridad.models import Rol
from tests import fabricas
from ventas.models import Venta

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_TI05_cobrar_la_vacuna_aplicada_no_vuelve_a_bajar_el_lote(client, crear_usuario):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    cobro = fabricas.servicio("Aplicación de vacuna", CategoriaServicio.APLICACION, 10)
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    max_ = fabricas.paciente("Max")
    aplicada = fabricas.aplicacion(max_, laura, vacuna, 365)  # lote de 20: queda en 19
    cita = aplicada.consulta.cita
    Cita.objects.filter(pk=cita.pk).update(estado=EstadoCita.COMPLETADA)
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))

    lista = client.get("/ventas/").content.decode()
    assert "Por cobrar hoy" in lista and f"/ventas/nuevo/?cita={cita.pk}" in lista

    propuesta = client.get(f"/ventas/nuevo/?cita={cita.pk}").content.decode()
    assert (
        f'value="s-{cita.servicio_id}" selected' in propuesta
        and f'value="s-{cobro.pk}" selected' in propuesta
    )
    datos = {
        "lineas-TOTAL_FORMS": "6",
        "lineas-INITIAL_FORMS": "2",
        "lineas-MIN_NUM_FORMS": "6",
        "lineas-MAX_NUM_FORMS": "20",
        "lineas-0-articulo": f"s-{cita.servicio_id}",
        "lineas-0-cantidad": "1",
        "lineas-1-articulo": f"s-{cobro.pk}",
        "lineas-1-cantidad": "1",
    }
    respuesta = client.post(f"/ventas/nuevo/?cita={cita.pk}", datos, follow=True)
    venta = Venta.objects.get()
    assert venta.cita_id == cita.pk and venta.total == Decimal("800.00")
    assert "Aplicación de vacuna" in respuesta.content.decode()

    # El lote bajó una sola vez, al aplicar; cobrar no agregó otro movimiento (RD-09)
    assert Lote.objects.get(producto=vacuna).cantidad_disponible == Decimal("19")
    assert list(MovimientoInventario.objects.filter(cantidad__lt=0).values_list("tipo", flat=True)) == [
        "Aplicación"
    ]

    # La cita ya no está por cobrar y volver a cobrarla lleva al ticket existente
    assert f"?cita={cita.pk}" not in client.get("/ventas/").content.decode()
    otra_vez = client.get(f"/ventas/nuevo/?cita={cita.pk}")
    assert otra_vez.status_code == 302 and otra_vez.url == f"/ventas/tickets/{venta.pk}/"
