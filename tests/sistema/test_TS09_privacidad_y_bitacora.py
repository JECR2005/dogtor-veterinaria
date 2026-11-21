"""TS-09 · Privacidad y auditoría (Tabla 4.15, RNF-03, RNF-08), por las pantallas, de principio a fin.

Método: registrar un cliente sin aviso, darlo de baja, exportar contactos y cancelar un ticket.
Criterio: no se guarda sin aviso; la baja conserva el historial; la exportación y la cancelación aparecen en
la bitácora.
"""

import csv
import io
from decimal import Decimal

import pytest

from catalogos.forms import MENSAJE_AVISO
from catalogos.models import (
    CategoriaServicio,
    Cliente,
    Especie,
    Mascota,
    PreferenciaContacto,
    Puesto,
    Raza,
    Sexo,
)
from clinico import services as clinico
from clinico.models import Consulta, ExpedienteClinico
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol
from tests import fabricas
from ventas import services as ventas
from ventas.models import Venta
from ventas.services import Partida

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

CLIENTE = {
    "nombre": "Lucía",
    "apellido_paterno": "Privacidad",
    "apellido_materno": "Ficticia",
    "telefono": "833 555-0101",
    "correo": "lucia@example.com",
    "direccion": "",
    "preferencia_contacto": PreferenciaContacto.CORREO,
    "rfc": "",
    "razon_social_fiscal": "",
    "regimen_fiscal": "",
    "cp_fiscal": "",
}


def test_TS09_aviso_baja_con_historial_exportacion_y_cancelacion_en_la_bitacora(client, crear_usuario):
    recepcion = crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    client.force_login(recepcion)

    # 1. Sin aceptar el aviso de privacidad no se guarda (RNF-08, RF-01)
    respuesta = client.post("/clientes/nuevo/", CLIENTE)
    assert MENSAJE_AVISO in respuesta.content.decode()
    assert not Cliente.objects.filter(apellido_paterno="Privacidad").exists()
    client.post("/clientes/nuevo/", {**CLIENTE, "acepto_aviso_privacidad": "on"})
    lucia = Cliente.objects.get(apellido_paterno="Privacidad")

    # Lucía tiene historial: una mascota con una consulta firmada y un ticket
    especie, _ = Especie.objects.get_or_create(nombre="Gato")
    raza, _ = Raza.objects.get_or_create(especie=especie, nombre="Mestizo")
    michi = Mascota.objects.create(cliente=lucia, raza=raza, nombre="Michi", sexo=Sexo.HEMBRA)
    ExpedienteClinico.objects.create(mascota=michi)
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    consulta_general = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    cita = fabricas.cita_de_hoy(michi, laura, consulta_general)
    consulta = clinico.abrir_consulta(cita, laura, {"sintomas": "Revisión", "peso_kg": Decimal("4.2")})
    datos = {"sintomas": "Revisión", "peso_kg": Decimal("4.2"), "diagnostico": "Sana"}
    clinico.guardar_consulta(consulta, laura, datos)
    clinico.firmar(consulta, laura)
    ticket = ventas.generar_ticket(lucia, recepcion.empleado, [Partida(servicio=consulta_general)], cita=cita)
    otro = fabricas.mascota("Rocky", "Pedro").cliente  # un cliente activo para la exportación

    # 2. La baja conserva el historial (baja lógica, RNF-08)
    client.post(f"/clientes/{lucia.pk}/baja/")
    lucia.refresh_from_db()
    assert not lucia.activo
    assert Mascota.objects.filter(cliente=lucia).count() == 1
    assert Consulta.objects.filter(expediente__mascota__cliente=lucia).count() == 1
    assert Venta.objects.filter(cliente=lucia).count() == 1
    baja = BitacoraAuditoria.objects.get(accion=AccionBitacora.BAJA_LOGICA, id_registro=lucia.pk)
    assert bitacora.valores_previos(baja)["activo"] is True

    # 3. Solo el Administrador exporta contactos; Lucía ya no sale y la exportación queda en la bitácora
    assert client.post("/bitacora/contactos/", {"acepto": "1"}).status_code == 403
    client.force_login(admin)
    texto = client.post("/bitacora/contactos/", {"acepto": "1"}).content.decode().lstrip("﻿")
    nombres = [fila[0] for fila in csv.reader(io.StringIO(texto))][1:]
    assert nombres == [otro.nombre]
    assert (
        BitacoraAuditoria.objects.filter(accion=AccionBitacora.EXPORTACION, entidad="contactos").count() == 1
    )

    # 4. La cancelación del ticket aparece en la bitácora con sus valores previos
    client.post(f"/ventas/tickets/{ticket.pk}/cancelar/", {"motivo": "Cliente dado de baja; se anula"})
    cancelacion = BitacoraAuditoria.objects.get(accion=AccionBitacora.CANCELACION, entidad="venta")
    assert (
        cancelacion.id_registro == ticket.pk
        and bitacora.valores_previos(cancelacion)["estado"] == "Pendiente"
    )

    pantalla = client.get("/bitacora/").content.decode()
    for texto_esperado in ("Baja lógica", "Exportación", "Contactos de clientes", "Cancelación", "Ticket"):
        assert texto_esperado in pantalla
