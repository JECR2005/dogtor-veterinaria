"""TI-06 · Ventas e Inventario (Tabla 4.13): vender un producto y cancelar el ticket.

Criterio: el stock baja al generar el ticket y se restaura al cancelarlo (RF-13, RF-14). Incluye S4-12 y el
adelanto de TI-09 (P5).
"""

from decimal import Decimal

import pytest

from catalogos.models import CategoriaProducto
from inventario.models import Lote
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol
from tests import fabricas
from ventas.models import Venta

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def escenario(client, crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    client.force_login(recepcion)
    collar = fabricas.producto(
        "ACC-001", "Collar ajustable", stock_minimo=0, categoria=CategoriaProducto.ACCESORIO, precio_venta=150
    )
    lote = fabricas.lote(collar, 12, None)
    cliente = fabricas.paciente("Max").cliente
    datos = {
        "lineas-TOTAL_FORMS": "6",
        "lineas-INITIAL_FORMS": "0",
        "lineas-MIN_NUM_FORMS": "6",
        "lineas-MAX_NUM_FORMS": "20",
        "lineas-0-articulo": f"p-{collar.pk}",
        "lineas-0-cantidad": "2",
    }
    client.post(f"/ventas/nuevo/?cliente={cliente.pk}", datos)
    return client, Venta.objects.get(), lote


def test_TI06_vender_y_cancelar_restaura_el_stock(escenario):
    client, venta, lote = escenario
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == 10  # bajó al generar el ticket

    url = f"/ventas/tickets/{venta.pk}/cancelar/"
    resumen = client.get(url).content.decode()
    assert "Regresan <strong>2 Dosis</strong> de Collar ajustable al lote" in resumen
    assert "No hay pagos que devolver." in resumen
    assert "Escriba el motivo de la cancelación." in client.post(url, {"motivo": ""}).content.decode()

    respuesta = client.post(url, {"motivo": "El cliente cambió de opinión"}, follow=True)
    contenido = respuesta.content.decode()
    assert f"Ticket {venta.folio_ticket} cancelado. Quedó registrado en la bitácora." in contenido
    assert "Ticket cancelado</strong> por" in contenido and "El cliente cambió de opinión" in contenido
    assert "Registrar pago" not in contenido and "Cancelar ticket" not in contenido  # solo lectura
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == 12  # se restauró
    assert client.get(url).status_code == 302  # ya cancelado: regresa al ticket


def test_S4_12_la_recepcionista_no_cancela_un_ticket_con_pagos(escenario):
    client, venta, lote = escenario
    client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Efectivo", "recibido": "100"})
    pantalla = client.get(f"/ventas/tickets/{venta.pk}/").content.decode()
    assert "solo el Administrador lo puede cancelar" in pantalla and "Cancelar ticket" not in pantalla

    url = f"/ventas/tickets/{venta.pk}/cancelar/"
    for respuesta in (client.get(url), client.post(url, {"motivo": "Intento"})):
        assert respuesta.status_code == 403 and "Acceso denegado" in respuesta.content.decode()
    venta.refresh_from_db()
    assert venta.estado == "Pendiente" and Lote.objects.get(pk=lote.pk).cantidad_disponible == 10


def test_S4_12_el_administrador_cancela_un_ticket_pagado_con_devolucion_reintegro_y_bitacora(
    escenario, crear_usuario
):
    """Adelanto de TI-09 (P5): devolución, reintegro y una entrada en la bitácora con los valores previos."""
    client, venta, lote = escenario
    client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Efectivo", "recibido": "500"})
    venta.refresh_from_db()
    assert venta.estado == "Pagada"

    administrador = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    client.force_login(administrador)
    url = f"/ventas/tickets/{venta.pk}/cancelar/"
    assert "devolución de $300.00 en efectivo" in client.get(url).content.decode()
    client.post(url, {"motivo": "Producto defectuoso"})

    venta.refresh_from_db()
    assert (venta.estado, venta.cancelo, venta.motivo_cancelacion) == (
        "Cancelada",
        administrador.empleado,
        "Producto defectuoso",
    )
    devolucion = venta.pagos.get(tipo="Devolución")
    assert (devolucion.metodo, devolucion.monto) == ("Efectivo", Decimal("300.00"))
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == 12
    registro = BitacoraAuditoria.objects.get(accion=AccionBitacora.CANCELACION)
    assert registro.usuario == administrador and registro.id_registro == venta.pk
    assert bitacora.valores_previos(registro)["estado"] == "Pagada"
