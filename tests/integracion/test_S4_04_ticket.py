"""S4-04 a S4-07 · UI-17 Ticket por las pantallas: cliente, líneas, generar, lista y detalle (RF-13)."""

from decimal import Decimal

import pytest
from django.utils import timezone

from catalogos.models import CategoriaProducto, CategoriaServicio
from inventario.models import Lote
from seguridad.models import Rol
from tests import fabricas
from ventas.models import Venta

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def mostrador(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    max_ = fabricas.paciente("Max")
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    croquetas = fabricas.producto(
        "ALI-001", "Croquetas perro", stock_minimo=0, categoria=CategoriaProducto.ALIMENTO, precio_venta=320
    )
    lote = fabricas.lote(croquetas, 10, 200)
    return client, max_.cliente, bano, croquetas, lote


def _lineas(*filas, total=6):
    datos = {
        "lineas-TOTAL_FORMS": str(total),
        "lineas-INITIAL_FORMS": "0",
        "lineas-MIN_NUM_FORMS": "6",
        "lineas-MAX_NUM_FORMS": "20",
    }
    for i in range(total):
        articulo, cantidad, folio = filas[i] if i < len(filas) else ("", "", "")
        datos.update(
            {
                f"lineas-{i}-articulo": articulo,
                f"lineas-{i}-cantidad": cantidad,
                f"lineas-{i}-folio_receta": folio,
            }
        )
    return datos


def test_S4_04_generar_un_ticket_desde_la_barra_superior(mostrador):
    client, cliente, bano, croquetas, lote = mostrador
    inicio = client.get("/").content.decode()
    assert 'href="/ventas/nuevo/"' in inicio  # botón «Nuevo ticket» de la Recepcionista

    eleccion = client.get("/ventas/nuevo/").content.decode()
    assert "Nuevo ticket · ¿para quién?" in eleccion and f"/ventas/nuevo/?cliente={cliente.pk}" in eleccion

    url = f"/ventas/nuevo/?cliente={cliente.pk}"
    formulario = client.get(url).content.decode()
    assert (
        "Croquetas perro (ALI-001) · $320.00 · hay 10 Dosis" in formulario and "Baño · $400.00" in formulario
    )

    datos = _lineas((f"p-{croquetas.pk}", "2", ""), (f"s-{bano.pk}", "1", ""))
    respuesta = client.post(url, datos, follow=True)
    venta = Venta.objects.get()
    contenido = respuesta.content.decode()
    assert f"Ticket {venta.folio_ticket} generado por $1,040.00. Registre el pago." in contenido
    assert respuesta.redirect_chain[-1][0] == f"/ventas/tickets/{venta.pk}/"
    assert "Pendiente" in contenido and 'data-saldo="1040.00"' in contenido
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == Decimal("8")  # baja al generar el ticket

    lista = client.get("/ventas/").content.decode()
    assert venta.folio_ticket in lista and "$1,040.00" in lista


def test_S4_04_sin_lineas_o_sin_stock_no_se_genera(mostrador):
    client, cliente, _, croquetas, lote = mostrador
    url = f"/ventas/nuevo/?cliente={cliente.pk}"
    assert (
        "Agregue al menos un producto o servicio al ticket." in client.post(url, _lineas()).content.decode()
    )
    contenido = client.post(url, _lineas((f"p-{croquetas.pk}", "11", ""))).content.decode()
    assert "Stock insuficiente: hay 10" in contenido
    assert not Venta.objects.exists() and Lote.objects.get(pk=lote.pk).cantidad_disponible == 10
    assert "Elija el producto o servicio." in client.post(url, _lineas(("", "2", ""))).content.decode()


def test_S4_04_solo_recepcion_y_administrador_venden(client, crear_usuario, mostrador):
    _, cliente, *_ = mostrador
    for rol in (Rol.VETERINARIO, Rol.ESTILISTA):
        client.force_login(crear_usuario(f"u_{rol.lower()}", rol=rol))
        assert client.get("/ventas/").status_code == 403
        assert client.get(f"/ventas/nuevo/?cliente={cliente.pk}").status_code == 403
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    assert client.get("/ventas/").status_code == 200
    assert client.get(f"/ventas/nuevo/?cliente={cliente.pk}").status_code == 200
