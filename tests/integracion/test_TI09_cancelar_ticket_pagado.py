"""TI-09 · Ventas, Inventario y Seguridad (Tabla 4.13): cancelar un ticket pagado como Administrador.

Criterio: se registran la devolución, el reintegro de los productos vendidos y una entrada en la bitácora con
los valores previos (RF-14, RNF-03). Completa el adelanto de P4: el ticket se genera y se cobra en pantalla
con dos métodos, el Administrador lo cancela y la cancelación se ve en la Bitácora (UI-20) con sus valores
previos.
"""

from decimal import Decimal

import pytest

from catalogos.models import CategoriaProducto, CategoriaServicio
from inventario.models import Lote, MovimientoInventario
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol
from tests import fabricas
from ventas.models import Venta

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_TI09_el_administrador_cancela_un_ticket_pagado_con_devolucion_reintegro_y_bitacora(
    client, crear_usuario
):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    administrador = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    croquetas = fabricas.producto(
        "ALI-001", "Croquetas", stock_minimo=0, categoria=CategoriaProducto.ALIMENTO, precio_venta=320
    )
    lote_a = fabricas.lote(croquetas, 1, 30, numero="A")
    lote_b = fabricas.lote(croquetas, 5, 200, numero="B")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    cliente = fabricas.paciente("Max").cliente

    # La recepcionista genera el ticket (2 croquetas: una de cada lote, y un baño) y lo cobra con dos métodos
    client.force_login(recepcion)
    client.post(
        f"/ventas/nuevo/?cliente={cliente.pk}",
        {
            "lineas-TOTAL_FORMS": "6",
            "lineas-INITIAL_FORMS": "0",
            "lineas-MIN_NUM_FORMS": "6",
            "lineas-MAX_NUM_FORMS": "20",
            "lineas-0-articulo": f"p-{croquetas.pk}",
            "lineas-0-cantidad": "2",
            "lineas-1-articulo": f"s-{bano.pk}",
            "lineas-1-cantidad": "1",
        },
    )
    venta = Venta.objects.get()
    assert venta.total == Decimal("1040.00")
    client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Tarjeta", "recibido": "640"})
    client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Efectivo", "recibido": "500"})
    venta.refresh_from_db()
    assert (venta.estado, venta.saldo) == ("Pagada", Decimal("0.00"))
    assert (
        Lote.objects.get(pk=lote_a.pk).cantidad_disponible,
        Lote.objects.get(pk=lote_b.pk).cantidad_disponible,
    ) == (
        0,
        4,
    )

    # La recepcionista no puede cancelar un ticket con pagos; el Administrador sí
    assert client.post(f"/ventas/tickets/{venta.pk}/cancelar/", {"motivo": "Error"}).status_code == 403
    assert Venta.objects.get(pk=venta.pk).estado == "Pagada"
    client.force_login(administrador)
    client.post(f"/ventas/tickets/{venta.pk}/cancelar/", {"motivo": "El cliente devolvió la compra"})

    venta.refresh_from_db()
    assert venta.estado == "Cancelada" and venta.saldo == venta.total
    # Devolución: una por cada método con que se pagó
    devoluciones = sorted(venta.pagos.filter(tipo="Devolución").values_list("metodo", "monto"))
    assert devoluciones == [("Efectivo", Decimal("400.00")), ("Tarjeta", Decimal("640.00"))]
    # Reintegro: cada croqueta regresa a su lote; el baño no toca el inventario
    assert Lote.objects.get(pk=lote_a.pk).cantidad_disponible == 1
    assert Lote.objects.get(pk=lote_b.pk).cantidad_disponible == 5
    assert MovimientoInventario.objects.filter(tipo="Devolución").count() == 2

    # Bitácora: la cancelación con los valores previos, y antes el ticket y los dos cobros de la recepcionista
    cancelacion = BitacoraAuditoria.objects.get(accion=AccionBitacora.CANCELACION, entidad="venta")
    assert cancelacion.usuario == administrador and cancelacion.id_registro == venta.pk
    previos = bitacora.valores_previos(cancelacion)
    assert (previos["estado"], previos["saldo"], previos["total"]) == ("Pagada", "0.00", "1040.00")
    assert BitacoraAuditoria.objects.filter(usuario=recepcion, entidad="venta", accion="Alta").count() == 1
    assert BitacoraAuditoria.objects.filter(usuario=recepcion, entidad="pago", accion="Alta").count() == 2

    # Y el Administrador la ve en UI-20 filtrando por acción
    pagina = client.get("/bitacora/", {"accion": "Cancelación"}).content.decode()
    assert "Ticket" in pagina and f"#{venta.pk}" in pagina and "Pagada" in pagina
