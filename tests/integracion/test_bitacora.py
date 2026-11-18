"""S1-07 · Bitácora de auditoría para bajas de clientes y reactivaciones de cuentas (RNF-03).

Criterio del plan: cada baja deja registro con sus valores previos.
"""

import pytest
from django.core.exceptions import PermissionDenied
from django.db import transaction

from catalogos import services as catalogos
from catalogos.models import Cliente, PreferenciaContacto
from seguridad import bitacora, services
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol, Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def cliente():
    return Cliente.objects.create(
        nombre="Lucía",
        apellido_paterno="Ficticia",
        telefono="8331234567",
        preferencia_contacto=PreferenciaContacto.choices[0][0],
        acepto_aviso_privacidad=True,
    )


@pytest.fixture
def recepcion(crear_usuario):
    return crear_usuario("recepcion", rol=Rol.RECEPCIONISTA)


def test_S1_07_la_baja_de_un_cliente_deja_registro_con_valores_previos(cliente, recepcion):
    catalogos.dar_de_baja_cliente(cliente, recepcion)

    assert Cliente.objects.get(pk=cliente.pk).activo is False
    registro = BitacoraAuditoria.objects.get()
    assert registro.usuario == recepcion
    assert registro.accion == AccionBitacora.BAJA_LOGICA
    assert registro.entidad == "cliente"
    assert registro.id_registro == cliente.pk
    assert registro.fecha_hora is not None
    previos = bitacora.valores_previos(registro)
    assert previos["activo"] is True
    assert previos["nombre"] == "Lucía"
    assert previos["telefono"] == "8331234567"


def test_un_cliente_ya_dado_de_baja_no_genera_otro_registro(cliente, recepcion):
    catalogos.dar_de_baja_cliente(cliente, recepcion)
    with pytest.raises(catalogos.OperacionNoValida, match="ya está dado de baja"):
        catalogos.dar_de_baja_cliente(cliente, recepcion)
    assert BitacoraAuditoria.objects.count() == 1


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.ADMINISTRADOR])
def test_solo_quien_tiene_clientes_completo_da_de_baja(cliente, crear_usuario, rol):
    usuario = crear_usuario("otro", rol=rol)  # Tabla 4.9: Clientes en consulta (○) para estos roles
    with pytest.raises(PermissionDenied):
        catalogos.dar_de_baja_cliente(cliente, usuario)
    assert Cliente.objects.get(pk=cliente.pk).activo is True
    assert not BitacoraAuditoria.objects.exists()


def test_si_la_bitacora_falla_la_baja_se_revierte(cliente, recepcion, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("bitácora no disponible")

    monkeypatch.setattr(bitacora, "registrar", falla)
    with pytest.raises(RuntimeError):
        catalogos.dar_de_baja_cliente(cliente, recepcion)
    assert Cliente.objects.get(pk=cliente.pk).activo is True


def test_S1_07_la_reactivacion_de_una_cuenta_deja_registro_sin_la_contrasena(crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cuenta = crear_usuario("estilista", rol=Rol.ESTILISTA)
    Usuario.objects.filter(pk=cuenta.pk).update(intentos_fallidos=5)

    services.reactivar_cuenta(cuenta, admin)

    registro = BitacoraAuditoria.objects.get()
    assert (registro.usuario, registro.accion, registro.entidad, registro.id_registro) == (
        admin,
        AccionBitacora.MODIFICACION,
        "usuario",
        cuenta.pk,
    )
    previos = bitacora.valores_previos(registro)
    assert previos["intentos_fallidos"] == 5
    assert previos["nombre_usuario"] == "estilista"
    assert "hash_contrasena" not in previos and "password" not in previos
    assert "pbkdf2" not in registro.valores_previos and "md5$" not in registro.valores_previos


def test_reactivar_una_cuenta_que_no_esta_bloqueada_no_registra_nada(crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cuenta = crear_usuario("estilista", rol=Rol.ESTILISTA)
    services.reactivar_cuenta(cuenta, admin)
    assert not BitacoraAuditoria.objects.exists()


def test_la_pantalla_de_reactivacion_registra_en_la_bitacora(client, crear_usuario):
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    cuenta = crear_usuario("recepcion")
    Usuario.objects.filter(pk=cuenta.pk).update(intentos_fallidos=5)
    client.force_login(admin)
    client.post(f"/cuenta/bloqueadas/{cuenta.pk}/reactivar/")
    assert BitacoraAuditoria.objects.filter(id_registro=cuenta.pk, usuario=admin).count() == 1


def test_registrar_rechaza_acciones_que_no_estan_en_la_tabla_3_57(cliente, recepcion):
    with pytest.raises(ValueError):
        bitacora.registrar(recepcion, "Borrado", cliente)


def test_registrar_fuera_de_una_transaccion_es_un_error(cliente, recepcion, monkeypatch):
    class SinTransaccion:
        in_atomic_block = False

    monkeypatch.setattr(transaction, "get_connection", lambda *a, **k: SinTransaccion())
    with pytest.raises(RuntimeError, match="transacción"):
        bitacora.registrar(recepcion, AccionBitacora.BAJA_LOGICA, cliente)


def test_valores_de_permite_elegir_campos(cliente):
    assert bitacora.valores_de(cliente, ["telefono", "activo"]) == {"telefono": "8331234567", "activo": True}
