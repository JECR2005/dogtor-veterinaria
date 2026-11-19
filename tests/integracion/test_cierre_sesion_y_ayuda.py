"""LV-03 puntos 9 y 10 · Cerrar sesión termina el acceso (DEF-003) y existe la Ayuda (DEF-004)."""

import pytest

from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def test_DEF003_las_paginas_con_sesion_no_se_guardan_en_la_cache(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    for ruta in ("/", "/clientes/", "/agenda/"):
        control = client.get(ruta)["Cache-Control"]
        assert "no-store" in control and "no-cache" in control and "private" in control


def test_DEF003_despues_de_cerrar_sesion_la_pagina_pide_entrar(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    client.post("/cuenta/salir/")
    respuesta = client.get("/clientes/")
    assert respuesta.status_code == 302 and respuesta.url.startswith("/cuenta/entrar/")


@pytest.mark.parametrize(
    "rol, texto",
    [
        (Rol.RECEPCIONISTA, "Agendar una cita"),
        (Rol.VETERINARIO, "Revisar sus citas"),
        (Rol.ESTILISTA, "Revisar sus citas"),
        (Rol.ADMINISTRADOR, "Empleados y cuentas"),
    ],
)
def test_DEF004_la_ayuda_muestra_la_guia_del_rol(client, crear_usuario, rol, texto):
    client.force_login(crear_usuario("usuario", rol=rol))
    inicio = client.get("/").content.decode()
    assert 'href="/ayuda/"' in inicio  # botón Ayuda en la barra superior
    ayuda = client.get("/ayuda/").content.decode()
    assert "Guía de usuario" in ayuda and texto in ayuda and "Problemas frecuentes" in ayuda


def test_S2_12_la_ayuda_del_administrador_explica_inventario_y_compras(client, crear_usuario):
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    ayuda = client.get("/ayuda/").content.decode()
    for texto in ("Productos y existencias", "Desechar", "Recibir un pedido", "Stock insuficiente"):
        assert texto in ayuda, texto


@pytest.mark.parametrize("rol", [Rol.RECEPCIONISTA, Rol.VETERINARIO, Rol.ESTILISTA])
def test_S2_12_los_demas_roles_no_ven_inventario_ni_compras(client, crear_usuario, rol):
    """RI-11: el menú no muestra las opciones y la Ayuda no las explica; el acceso directo lo cubre TS-01."""
    client.force_login(crear_usuario("usuario", rol=rol))
    inicio = client.get("/").content.decode()
    assert 'href="/inventario/productos/"' not in inicio and 'href="/compras/proveedores/"' not in inicio
    assert 'data-aviso="inventario"' not in inicio
    assert "Recibir un pedido" not in client.get("/ayuda/").content.decode()
