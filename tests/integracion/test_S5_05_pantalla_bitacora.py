"""S5-05 y S5-06 · UI-20 Bitácora y exportación: solo el Administrador (Tabla 4.9, RNF-03, RNF-08).

Criterios del plan: consulta por fecha, usuario y acción; la exportación de la bitácora y la de contactos
quedan registradas; los clientes dados de baja no salen en los contactos.
"""

import csv
import io
from datetime import timedelta

import pytest
from django.utils import timezone

from catalogos import services as catalogos
from catalogos.models import Cliente, PreferenciaContacto
from inventario import services as inventario
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def _csv(respuesta):
    texto = b"".join(respuesta.streaming_content if respuesta.streaming else [respuesta.content]).decode()
    assert texto.startswith("﻿")  # Excel abre bien los acentos
    return list(csv.reader(io.StringIO(texto.lstrip("﻿"))))


@pytest.fixture
def escenario(client, crear_usuario):
    """La recepcionista da de baja a Ana y a Carla; Beto sigue activo."""
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    sofia = crear_usuario("sofia", rol=Rol.RECEPCIONISTA)
    ana = fabricas.mascota("Firulais", "Ana").cliente
    beto = Cliente.objects.create(
        nombre="Beto",
        apellido_paterno="Ficticio",
        telefono="8330000002",
        correo="beto@example.com",
        preferencia_contacto=PreferenciaContacto.CORREO,
        acepto_aviso_privacidad=True,
    )
    carla = Cliente.objects.create(
        nombre="Carla",
        apellido_paterno="Ficticia",
        telefono="8330000003",
        preferencia_contacto=PreferenciaContacto.TELEFONO,
        acepto_aviso_privacidad=True,
    )
    catalogos.dar_de_baja_cliente(ana, sofia)
    catalogos.dar_de_baja_cliente(carla, sofia)
    client.force_login(admin)
    return client, admin, sofia, {"ana": ana, "beto": beto, "carla": carla}


def test_S5_05_lista_los_registros_con_sus_valores_previos(escenario):
    client, _, _, clientes = escenario
    respuesta = client.get("/bitacora/")
    pagina = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "2 registros" in pagina and "Baja lógica" in pagina and "sofia" in pagina
    assert f"#{clientes['ana'].pk}" in pagina and "Ana" in pagina  # valores previos: el nombre que tenía


def test_S5_05_filtra_por_usuario_accion_que_y_fecha(escenario):
    client, admin, sofia, _ = escenario
    assert "2 registros" in client.get("/bitacora/", {"usuario": sofia.pk}).content.decode()
    assert "0 registros" in client.get("/bitacora/", {"usuario": admin.pk}).content.decode()
    assert "0 registros" in client.get("/bitacora/", {"accion": "Exportación"}).content.decode()
    assert "2 registros" in client.get("/bitacora/", {"entidad": "cliente"}).content.decode()
    ayer = timezone.localdate() - timedelta(days=1)
    pasado = client.get("/bitacora/", {"desde": ayer - timedelta(days=5), "hasta": ayer}).content.decode()
    assert "0 registros" in pasado
    invertido = client.get("/bitacora/", {"desde": timezone.localdate(), "hasta": ayer}).content.decode()
    assert "posterior a «Hasta»" in invertido


def test_S5_05_exportar_lo_filtrado_y_la_exportacion_queda_registrada(escenario):
    client, admin, sofia, _ = escenario
    assert client.get("/bitacora/exportar/").status_code == 405  # deja registro: solo con POST
    hoy = timezone.localdate().isoformat()
    respuesta = client.post(
        "/bitacora/exportar/", {"desde": hoy, "hasta": hoy, "usuario": sofia.pk, "accion": "Baja lógica"}
    )
    assert respuesta["Content-Type"].startswith("text/csv")
    assert "attachment" in respuesta["Content-Disposition"]
    filas = _csv(respuesta)
    assert filas[0] == bitacora.COLUMNAS_CSV
    assert len(filas) == 3 and {fila[1] for fila in filas[1:]} == {"sofia"}

    exportacion = BitacoraAuditoria.objects.get(accion=AccionBitacora.EXPORTACION)
    assert (exportacion.usuario, exportacion.entidad, exportacion.id_registro) == (
        admin,
        "bitacora_auditoria",
        0,
    )
    detalle = bitacora.valores_previos(exportacion)
    assert detalle["registros"] == 2 and detalle["filtros"]["usuario"] == "sofia"


def test_S5_06_exportar_contactos_sin_los_dados_de_baja_y_con_registro(escenario):
    client, admin, _, clientes = escenario
    assert client.get("/bitacora/contactos/").status_code == 405
    sin_confirmar = client.post("/bitacora/contactos/", follow=True)
    assert "Confirme que los contactos" in sin_confirmar.content.decode()
    assert not BitacoraAuditoria.objects.filter(accion=AccionBitacora.EXPORTACION).exists()

    filas = _csv(client.post("/bitacora/contactos/", {"acepto": "1"}))
    assert filas[0][:4] == ["Nombre", "Apellido paterno", "Apellido materno", "Teléfono"]
    assert [fila[0] for fila in filas[1:]] == ["Beto"]  # Ana y Carla están dadas de baja (RNF-08)
    assert filas[1][4:] == ["beto@example.com", "Correo"]
    registro = BitacoraAuditoria.objects.get(accion=AccionBitacora.EXPORTACION, entidad="contactos")
    assert registro.usuario == admin and bitacora.valores_previos(registro)["registros"] == 1
    assert "Contactos de clientes" in client.get("/bitacora/").content.decode()


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA])
def test_S5_05_solo_el_administrador(client, crear_usuario, rol):
    client.force_login(crear_usuario("otro", rol=rol))
    for url in ("/bitacora/", "/bitacora/exportar/", "/bitacora/contactos/"):
        assert client.get(url).status_code == 403
        assert client.post(url, {"acepto": "1"}).status_code == 403
    assert not BitacoraAuditoria.objects.exists()


def test_S5_05_pagina_de_50_en_50(client, crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    producto = fabricas.producto("ALI-P", "Croquetas", stock_minimo=0)
    for numero in range(55):
        inventario.registrar_entrada(producto, f"L-{numero}", 1, admin.empleado)
    client.force_login(admin)
    primera = client.get("/bitacora/", {"entidad": "movimiento_inventario"}).content.decode()
    assert "55 registros" in primera and "Página 1 de 2" in primera
    assert "entidad=movimiento_inventario&pagina=2" in primera  # la paginación conserva los filtros
    assert "Página 2 de 2" in client.get("/bitacora/", {"pagina": 2}).content.decode()


def test_S5_06_el_administrador_ve_el_acceso_desde_clientes(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    assert "/bitacora/#contactos" in client.get("/clientes/").content.decode()
    client.force_login(crear_usuario("sofia", rol=Rol.RECEPCIONISTA))
    assert "/bitacora/#contactos" not in client.get("/clientes/").content.decode()


def test_S5_05_ayuda_del_administrador(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    ayuda = client.get("/ayuda/").content.decode()
    for tema in ("Revisar la bitácora", "Exportar contactos de clientes", "Corregir una consulta firmada"):
        assert tema in ayuda
    client.force_login(crear_usuario("laura", rol=Rol.VETERINARIO))
    assert "Revisar la bitácora" not in client.get("/ayuda/").content.decode()
