"""TI-07 · Expediente clínico y Ventas (Tabla 4.13): vender un medicamento con control con el folio de
una receta emitida. Criterio: la línea se acepta solo con el folio de una receta que incluye el producto
(RD-12)."""

from decimal import Decimal

import pytest

from catalogos.models import CategoriaProducto, CategoriaServicio, Puesto
from clinico.services import abrir_consulta, emitir_receta
from inventario.models import Lote
from seguridad.models import Rol
from tests import fabricas
from ventas.models import Venta

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_TI07_el_medicamento_con_control_solo_se_vende_con_su_receta(client, crear_usuario):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    max_ = fabricas.paciente("Max")
    amoxicilina = fabricas.producto(
        "MED-001",
        "Amoxicilina 250 mg",
        stock_minimo=0,
        categoria=CategoriaProducto.MEDICAMENTO,
        requiere_receta=True,
    )
    lote = fabricas.lote(amoxicilina, 30, 200)
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = abrir_consulta(cita, laura, {"sintomas": "Otitis", "peso_kg": Decimal("28")})
    receta = emitir_receta(consulta, laura, [(amoxicilina, "1 tableta", "Cada 12 horas", 7, None)])
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))

    url = f"/ventas/nuevo/?cliente={max_.cliente_id}"
    assert (
        "Amoxicilina 250 mg (MED-001) · $150.00 · hay 30 Dosis · requiere receta"
        in client.get(url).content.decode()
    )

    def linea(folio):
        return {
            "lineas-TOTAL_FORMS": "6",
            "lineas-INITIAL_FORMS": "0",
            "lineas-MIN_NUM_FORMS": "6",
            "lineas-MAX_NUM_FORMS": "20",
            "lineas-0-articulo": f"p-{amoxicilina.pk}",
            "lineas-0-cantidad": "14",
            "lineas-0-folio_receta": folio,
        }

    sin_folio = client.post(url, linea("")).content.decode()
    assert "«Amoxicilina 250 mg» requiere receta: capture el folio de la receta (RD-12)." in sin_folio
    assert not Venta.objects.exists() and Lote.objects.get(pk=lote.pk).cantidad_disponible == 30

    respuesta = client.post(url, linea(receta.folio), follow=True)
    venta = Venta.objects.get()
    assert venta.detalles.get().receta == receta
    assert f"Receta {receta.folio}" in respuesta.content.decode()
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == 16
