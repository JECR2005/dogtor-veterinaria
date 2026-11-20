"""S4-15 · Interfaz y seguridad de P4: Tabla 4.9 en Ventas y caja y Ayuda de Recepción y Administrador.

Tabla 4.9: Ventas y caja ● para el Administrador y ● para la Recepcionista «sin cancelar tickets con pagos»;
Veterinario y Estilista sin acceso. TS-01 recorre además todas las rutas con los cuatro roles.
"""

from decimal import Decimal

import pytest

from catalogos.models import CategoriaServicio
from seguridad.models import Rol
from tests import fabricas
from ventas.services import Partida, generar_ticket, registrar_pago

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def pagado(crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    venta = generar_ticket(fabricas.paciente("Max").cliente, recepcion.empleado, [Partida(servicio=bano)])
    registrar_pago(venta, recepcion.empleado, "Efectivo", Decimal("400"))
    return recepcion, venta


def _rutas(venta):
    base = f"/ventas/tickets/{venta.pk}/"
    return [
        "/ventas/",
        "/ventas/nuevo/",
        "/ventas/corte/",
        "/ventas/corte/pdf/",
        base,
        f"{base}pdf/",
        f"{base}cancelar/",
    ]


def test_S4_15_la_recepcionista_ve_todo_menos_cancelar_un_ticket_con_pagos(client, pagado):
    recepcion, venta = pagado
    client.force_login(recepcion)
    for ruta in _rutas(venta):
        esperado = 403 if ruta.endswith("cancelar/") else 200
        assert client.get(ruta).status_code == esperado, ruta


def test_S4_15_el_administrador_cancela_un_ticket_con_pagos(client, crear_usuario, pagado):
    _, venta = pagado
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    for ruta in _rutas(venta):
        assert client.get(ruta).status_code == 200, ruta


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA])
def test_S4_15_veterinario_y_estilista_no_entran_a_ventas(client, crear_usuario, pagado, rol):
    _, venta = pagado
    client.force_login(crear_usuario("usuario", rol=rol))
    for ruta in _rutas(venta):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 403 and "Acceso denegado" in respuesta.content.decode(), ruta
    inicio = client.get("/").content.decode()
    assert 'href="/ventas/' not in inicio and "Tickets con saldo" not in inicio


@pytest.mark.parametrize(
    "rol, textos",
    [
        (
            Rol.RECEPCIONISTA,
            [
                "Cobrar en caja",
                "Cancelar un ticket",
                "Corte de caja",
                "requiere receta: capture el folio",
                "Solo puede cancelar tickets <strong>sin pagos</strong>",
            ],
        ),
        (
            Rol.ADMINISTRADOR,
            ["Ventas y caja", "Solo usted cancela un ticket <strong>con pagos</strong>", "Corte de caja"],
        ),
    ],
)
def test_S4_15_la_ayuda_explica_ventas_y_caja(client, crear_usuario, rol, textos):
    client.force_login(crear_usuario("usuario", rol=rol))
    ayuda = client.get("/ayuda/").content.decode()
    for texto in textos:
        assert texto in ayuda, texto


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA])
def test_S4_15_la_ayuda_de_otros_roles_no_explica_la_caja(client, crear_usuario, rol):
    client.force_login(crear_usuario("usuario", rol=rol))
    ayuda = client.get("/ayuda/").content.decode()
    assert "Cobrar en caja" not in ayuda and "Corte de caja" not in ayuda
