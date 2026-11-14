"""S1-08 · UI-05 Clientes: búsqueda, alta con aviso obligatorio, edición y baja lógica (RF-01, RNF-08).

Criterio del plan: sin aviso no se guarda; el dado de baja no aparece en búsquedas.
"""

import pytest

from catalogos import services
from catalogos.forms import MENSAJE_AVISO
from catalogos.models import Cliente, Especie, Mascota, PreferenciaContacto, Raza, Sexo
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

DATOS = {
    "nombre": "Ana",
    "apellido_paterno": "López",
    "apellido_materno": "Ficticia",
    "telefono": "833 123-4567",
    "correo": "",
    "direccion": "",
    "preferencia_contacto": PreferenciaContacto.WHATSAPP,
    "rfc": "",
    "razon_social_fiscal": "",
    "regimen_fiscal": "",
    "cp_fiscal": "",
    "acepto_aviso_privacidad": "on",
}


def _cliente(nombre="Bruno", apellido="Martínez", telefono="8339876543", activo=True):
    return Cliente.objects.create(
        nombre=nombre,
        apellido_paterno=apellido,
        telefono=telefono,
        preferencia_contacto=PreferenciaContacto.TELEFONO,
        acepto_aviso_privacidad=True,
        activo=activo,
    )


def _mascota(cliente, nombre):
    especie, _ = Especie.objects.get_or_create(nombre="Perro")
    raza, _ = Raza.objects.get_or_create(especie=especie, nombre="Mestizo")
    return Mascota.objects.create(cliente=cliente, raza=raza, nombre=nombre, sexo=Sexo.MACHO)


@pytest.fixture
def recepcion(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    return client


@pytest.fixture
def administrador(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    return client


# --- Alta ---------------------------------------------------------------------
def test_S1_08_sin_aviso_de_privacidad_no_se_guarda(recepcion):
    datos = {**DATOS}
    del datos["acepto_aviso_privacidad"]
    respuesta = recepcion.post("/clientes/nuevo/", datos)
    assert respuesta.status_code == 200
    assert MENSAJE_AVISO in respuesta.content.decode()
    assert not Cliente.objects.exists()


def test_alta_con_aviso_guarda_y_abre_la_ficha(recepcion):
    respuesta = recepcion.post("/clientes/nuevo/", {**DATOS, "rfc": "loaa800101ab1"}, follow=True)
    cliente = Cliente.objects.get()
    assert respuesta.redirect_chain[-1][0] == f"/clientes/{cliente.pk}/"
    assert "registrado" in respuesta.content.decode()
    assert cliente.telefono == "8331234567"  # se guardan solo los dígitos
    assert cliente.rfc == "LOAA800101AB1"
    assert cliente.correo is None and cliente.direccion is None  # vacío se guarda como NULL
    assert cliente.acepto_aviso_privacidad and cliente.activo


@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"telefono": "12345"}, "10 dígitos"),
        ({"rfc": "NO-ES-RFC"}, "RFC no tiene un formato válido"),
        ({"cp_fiscal": "8900"}, "5 dígitos"),
        ({"regimen_fiscal": "6O5"}, "3 dígitos"),
        ({"preferencia_contacto": PreferenciaContacto.CORREO}, "capture su correo"),
        ({"nombre": ""}, "obligatorio"),
    ],
)
def test_alta_rechaza_datos_invalidos_con_su_mensaje(recepcion, cambio, mensaje):
    respuesta = recepcion.post("/clientes/nuevo/", {**DATOS, **cambio})
    assert mensaje in respuesta.content.decode()
    assert not Cliente.objects.exists()


# --- Búsqueda -----------------------------------------------------------------
def test_busqueda_por_nombre_apellido_telefono_y_mascota():
    ana = _cliente("Ana", "López", "8331112222")
    bruno = _cliente("Bruno", "Martínez", "8333334444")
    _mascota(bruno, "Firulais")

    assert list(services.buscar_clientes("ana")) == [ana]
    assert list(services.buscar_clientes("martinez")) == [bruno]  # sin acento también (intercalación CI_AS)
    assert list(services.buscar_clientes("3334")) == [bruno]
    assert list(services.buscar_clientes("firu")) == [bruno]
    assert list(services.buscar_clientes("ana 1112")) == [ana]  # todas las palabras deben coincidir
    assert list(services.buscar_clientes("ana firulais")) == []


def test_cada_cliente_aparece_una_vez_con_su_numero_de_mascotas():
    bruno = _cliente()
    _mascota(bruno, "Firulais")
    _mascota(bruno, "Fido")
    resultado = list(services.buscar_clientes("fi"))
    assert resultado == [bruno]
    assert resultado[0].total_mascotas == 2


def test_S1_08_el_dado_de_baja_no_aparece_en_busquedas(recepcion):
    _cliente("Carla", "Baja", activo=False)
    assert not services.buscar_clientes("carla").exists()
    assert "Carla" not in recepcion.get("/clientes/?q=carla").content.decode()
    # aunque la recepcionista pida ver bajas en la dirección, no se le muestran
    assert "Carla" not in recepcion.get("/clientes/?q=carla&bajas=1").content.decode()


def test_el_administrador_puede_consultar_a_los_dados_de_baja(administrador):
    carla = _cliente("Carla", "Baja", activo=False)
    contenido = administrador.get("/clientes/?q=carla&bajas=1").content.decode()
    assert "Carla" in contenido and "Dado de baja" in contenido
    ficha = administrador.get(f"/clientes/{carla.pk}/").content.decode()
    assert "Cliente dado de baja." in ficha


def test_la_ficha_de_un_dado_de_baja_no_abre_para_otros_roles(recepcion):
    carla = _cliente("Carla", "Baja", activo=False)
    assert recepcion.get(f"/clientes/{carla.pk}/").status_code == 404


def test_la_busqueda_global_de_la_barra_superior_lleva_a_clientes(recepcion):
    contenido = recepcion.get("/").content.decode()
    assert 'action="/clientes/"' in contenido


# --- Ficha, edición y baja ----------------------------------------------------
def test_la_ficha_lista_las_mascotas_del_cliente(recepcion):
    bruno = _cliente()
    _mascota(bruno, "Firulais")
    contenido = recepcion.get(f"/clientes/{bruno.pk}/").content.decode()
    assert "Firulais" in contenido and "Mestizo" in contenido and "Perro" in contenido


def test_edicion_guarda_cambios_sin_volver_a_pedir_el_aviso(recepcion):
    bruno = _cliente()
    contenido = recepcion.get(f"/clientes/{bruno.pk}/editar/").content.decode()
    assert "acepto_aviso_privacidad" not in contenido
    datos = {**DATOS, "nombre": "Bruno", "apellido_paterno": "Martínez", "telefono": "8330001111"}
    del datos["acepto_aviso_privacidad"]
    recepcion.post(f"/clientes/{bruno.pk}/editar/", datos)
    bruno.refresh_from_db()
    assert bruno.telefono == "8330001111"
    assert bruno.preferencia_contacto == PreferenciaContacto.WHATSAPP
    assert bruno.acepto_aviso_privacidad


def test_baja_desde_la_pantalla_con_confirmacion_y_bitacora(recepcion):
    bruno = _cliente()
    assert "¿Dar de baja" in recepcion.get(f"/clientes/{bruno.pk}/baja/confirmar/").content.decode()
    assert recepcion.get(f"/clientes/{bruno.pk}/baja/").status_code == 405  # solo por POST
    respuesta = recepcion.post(f"/clientes/{bruno.pk}/baja/", follow=True)
    assert "dado de baja" in respuesta.content.decode()
    bruno.refresh_from_db()
    assert not bruno.activo
    assert BitacoraAuditoria.objects.filter(
        accion=AccionBitacora.BAJA_LOGICA, entidad="cliente", id_registro=bruno.pk
    ).exists()


def test_un_dado_de_baja_no_se_edita(recepcion):
    carla = _cliente("Carla", "Baja", activo=False)
    assert recepcion.get(f"/clientes/{carla.pk}/editar/").status_code == 404


# --- Permisos (Tabla 4.9: Clientes ● Recepcionista, ○ los demás) --------------
@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.ADMINISTRADOR])
def test_los_roles_de_consulta_buscan_y_ven_pero_no_modifican(client, crear_usuario, rol):
    bruno = _cliente()
    client.force_login(crear_usuario("usuario", rol=rol))
    lista = client.get("/clientes/")
    assert lista.status_code == 200
    assert "Nuevo cliente" not in lista.content.decode()
    ficha = client.get(f"/clientes/{bruno.pk}/").content.decode()
    assert "Dar de baja" not in ficha and "Editar" not in ficha
    assert client.get("/clientes/nuevo/").status_code == 403
    assert client.post("/clientes/nuevo/", DATOS).status_code == 403
    assert client.get(f"/clientes/{bruno.pk}/editar/").status_code == 403
    assert client.post(f"/clientes/{bruno.pk}/baja/").status_code == 403
    bruno.refresh_from_db()
    assert bruno.activo
