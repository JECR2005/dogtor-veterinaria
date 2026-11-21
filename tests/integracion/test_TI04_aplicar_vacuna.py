"""TI-04 · Expediente clínico, Inventario y Recordatorios (Tabla 4.13): aplicar una vacuna en una consulta.

Criterio: el lote baja una sola vez con un movimiento de tipo Aplicación; la próxima dosis queda en el
historial y genera su recordatorio
72 horas antes (RF-08, RF-09, RD-05, RD-09).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from catalogos.models import CategoriaServicio, Puesto
from clinico.models import Aplicacion, Consulta
from inventario.models import Lote, MovimientoInventario
from recordatorios import services as recordatorios
from recordatorios.models import Recordatorio, TipoRecordatorio
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def escenario(client):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    client.force_login(fabricas.cuenta(laura, "laura", rol=Rol.VETERINARIO))
    max_ = fabricas.paciente("Max")
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Vacunación", CategoriaServicio.VACUNACION, 20)
    )
    client.post(f"/clinica/citas/{cita.pk}/atender/", {"sintomas": "Vacunación anual", "peso_kg": "28"})
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    lote = fabricas.lote(vacuna, 10, 200, numero="VAC-002-A")
    return client, Consulta.objects.get(cita=cita), vacuna, lote, max_


def test_TI04_aplicar_una_vacuna_dentro_de_una_consulta(escenario):
    client, consulta, vacuna, lote, max_ = escenario
    proxima = HOY + timedelta(days=365)
    formulario = client.get(f"/clinica/consultas/{consulta.pk}/").content.decode()
    assert "se tomará del lote VAC-002-A" in formulario  # UI-12: el lote sugerido por caducidad
    datos = {"producto": vacuna.pk, "cantidad": "1", "dosis": "1 mL SC", "proxima_fecha": proxima.isoformat()}
    respuesta = client.post(f"/clinica/consultas/{consulta.pk}/aplicar/", datos, follow=True)
    assert "Aplicación registrada: Vacuna antirrábica, lote VAC-002-A." in respuesta.content.decode()

    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == Decimal("9")  # baja una sola vez
    assert list(MovimientoInventario.objects.values_list("tipo", "cantidad")) == [
        ("Aplicación", Decimal("-1"))
    ]
    historial = client.get(f"/clinica/mascotas/{max_.pk}/historial/").content.decode()
    assert f"próxima {proxima:%d/%m/%Y}" in historial
    assert Aplicacion.objects.get().proxima_fecha == proxima

    # RF-09: la próxima dosis genera su recordatorio cuando faltan 3 días, no antes
    assert recordatorios.generar(HOY) == 0
    assert recordatorios.generar(proxima - timedelta(days=3)) == 1
    recordatorio = Recordatorio.objects.get()
    assert recordatorio.aplicacion == Aplicacion.objects.get() and recordatorio.cliente_id == max_.cliente_id
    assert recordatorio.fecha_objetivo == proxima and recordatorio.tipo == TipoRecordatorio.PROXIMA_DOSIS


def test_TI04_sin_proxima_fecha_la_pantalla_lo_dice_y_no_descuenta(escenario):
    client, consulta, vacuna, lote, _ = escenario
    datos = {"producto": vacuna.pk, "cantidad": "1", "dosis": "1 mL SC", "proxima_fecha": ""}
    contenido = client.post(f"/clinica/consultas/{consulta.pk}/aplicar/", datos).content.decode()
    assert "la próxima fecha es obligatoria" in contenido
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == Decimal("10")
