"""S4-08 a S4-10 · Cobro por las pantallas: pagos parciales con cambio, «Requiere factura» y PDF (RF-13)."""

from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from catalogos.models import CategoriaServicio
from seguridad.models import Rol
from tests import fabricas
from ventas.services import Partida, generar_ticket

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def ticket(client, crear_usuario):
    usuario = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    client.force_login(usuario)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    venta = generar_ticket(fabricas.paciente("Max").cliente, usuario.empleado, [Partida(servicio=bano)])
    return client, venta  # $400.00


def test_S4_08_abono_con_tarjeta_y_liquidacion_en_efectivo_con_cambio(ticket):
    client, venta = ticket
    url = f"/ventas/tickets/{venta.pk}/"
    pantalla = client.get(url).content.decode()
    assert "Registrar pago · saldo $400.00" in pantalla and 'value="400.00"' in pantalla

    datos = {"metodo": "Tarjeta", "recibido": "150", "referencia": "AUT 998877"}
    contenido = client.post(f"{url}pagar/", datos, follow=True).content.decode()
    assert "Pago de $150.00 en tarjeta registrado. Saldo: $250.00." in contenido
    assert 'data-saldo="250.00"' in contenido and "Pendiente" in contenido

    contenido = client.post(
        f"{url}pagar/", {"metodo": "Efectivo", "recibido": "300"}, follow=True
    ).content.decode()
    assert "Pago de $250.00 en efectivo registrado. Entregue $50.00 de cambio. Ticket pagado." in contenido
    assert "Registrar pago" not in contenido  # ya no hay saldo
    venta.refresh_from_db()
    assert (venta.estado, venta.saldo) == ("Pagada", Decimal("0.00"))
    assert [(p.metodo, p.monto) for p in venta.pagos.order_by("id_pago")] == [
        ("Tarjeta", Decimal("150.00")),
        ("Efectivo", Decimal("250.00")),
    ]


def test_S4_08_con_tarjeta_no_se_cobra_mas_que_el_saldo(ticket):
    client, venta = ticket
    contenido = client.post(
        f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Transferencia", "recibido": "500"}
    ).content.decode()
    assert "Con transferencia se cobra como máximo el saldo ($400.00)" in contenido
    assert not venta.pagos.exists()


def test_S4_09_requiere_factura_pide_los_datos_fiscales(ticket):
    client, venta = ticket
    url = f"/ventas/tickets/{venta.pk}/"
    pantalla = client.get(url).content.decode()
    assert "falta en la ficha del cliente: RFC, régimen fiscal, código postal fiscal" in pantalla
    contenido = client.post(f"{url}factura/", {"requiere": "si"}, follow=True).content.decode()
    assert "Para facturar, capture en la ficha de" in contenido
    cliente = venta.cliente
    cliente.rfc, cliente.regimen_fiscal, cliente.cp_fiscal = "LOAA800101AB1", "612", "89000"
    cliente.save()
    contenido = client.post(f"{url}factura/", {"requiere": "si"}, follow=True).content.decode()
    assert "requiere factura con los datos fiscales" in contenido and "RFC LOAA800101AB1" in contenido
    venta.refresh_from_db()
    assert venta.requiere_factura


def test_S4_10_pdf_del_ticket_en_tamano_carta(ticket):
    client, venta = ticket
    respuesta = client.get(f"/ventas/tickets/{venta.pk}/pdf/")
    assert respuesta["Content-Type"] == "application/pdf"
    assert f"Ticket-{venta.folio_ticket}.pdf" in respuesta["Content-Disposition"]
    pagina = PdfReader(BytesIO(respuesta.content)).pages[0]
    texto = pagina.extract_text()
    assert venta.folio_ticket in texto and "Baño" in texto and "$400.00" in texto
    ancho, alto = float(pagina.mediabox.width), float(pagina.mediabox.height)
    assert (round(ancho), round(alto)) == (612, 792)  # carta: 8.5 × 11 pulgadas


def test_S4_08_el_administrador_tambien_cobra_y_el_veterinario_no(client, crear_usuario, ticket):
    _, venta = ticket
    client.force_login(crear_usuario("vet", rol=Rol.VETERINARIO))
    respuesta = client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Efectivo", "recibido": "400"})
    assert respuesta.status_code == 403 and not venta.pagos.exists()
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    client.post(f"/ventas/tickets/{venta.pk}/pagar/", {"metodo": "Efectivo", "recibido": "400"})
    venta.refresh_from_db()
    assert venta.estado == "Pagada"
