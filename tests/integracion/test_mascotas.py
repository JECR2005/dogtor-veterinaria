"""S1-09 · UI-06 Mascotas: alta con su expediente en la misma transacción (RF-02, RD-10).

TI-01 (Tabla 4.13): alta de un cliente con aviso de privacidad y de su mascota. No se guarda el cliente
sin el aviso; la mascota queda ligada a él con un único expediente; un segundo expediente se rechaza.
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalogos import services
from catalogos.forms import MENSAJE_AVISO
from catalogos.models import Cliente, Especie, EstatusMascota, Mascota, PreferenciaContacto, Raza, Sexo
from clinico.models import ExpedienteClinico
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def raza():
    perro, _ = Especie.objects.get_or_create(nombre="Perro")
    gato, _ = Especie.objects.get_or_create(nombre="Gato")
    Raza.objects.get_or_create(especie=gato, nombre="Siamés")
    return Raza.objects.get_or_create(especie=perro, nombre="Schnauzer")[0]


@pytest.fixture
def cliente():
    return Cliente.objects.create(
        nombre="Bruno",
        apellido_paterno="Martínez",
        telefono="8339876543",
        preferencia_contacto=PreferenciaContacto.TELEFONO,
        acepto_aviso_privacidad=True,
    )


@pytest.fixture
def recepcion(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    return client


def _datos(raza, /, **cambios):
    datos = {
        "nombre": "Firulais",
        "raza": raza.pk,
        "sexo": Sexo.MACHO,
        "fecha_nacimiento": "2022-03-15",
        "peso_actual": "8.40",
        "color": "Gris sal y pimienta",
        "esterilizado": "on",
        "alergias": "Penicilina",
        "antecedentes": "",
    }
    datos.update(cambios)
    return datos


# --- TI-01 --------------------------------------------------------------------
def test_TI01_cliente_con_aviso_y_mascota_con_un_unico_expediente(recepcion, raza):
    # 1. Sin aviso de privacidad el cliente no se guarda
    cliente_datos = {
        "nombre": "Ana",
        "apellido_paterno": "López",
        "telefono": "8331234567",
        "preferencia_contacto": PreferenciaContacto.WHATSAPP,
    }
    assert MENSAJE_AVISO in recepcion.post("/clientes/nuevo/", cliente_datos).content.decode()
    assert not Cliente.objects.exists()

    # 2. Con aviso se guarda
    recepcion.post("/clientes/nuevo/", {**cliente_datos, "acepto_aviso_privacidad": "on"})
    ana = Cliente.objects.get()

    # 3. La mascota queda ligada a ella y se abre su expediente al guardar
    respuesta = recepcion.post(f"/clientes/{ana.pk}/mascotas/nueva/", _datos(raza), follow=True)
    mascota = Mascota.objects.get()
    assert mascota.cliente == ana
    assert respuesta.redirect_chain[-1][0] == f"/clientes/mascotas/{mascota.pk}/"
    assert "expediente abierto" in respuesta.content.decode()
    expediente = ExpedienteClinico.objects.get(mascota=mascota)
    assert expediente.alergias == "Penicilina"
    assert expediente.fecha_apertura == timezone.localdate()

    # 4. Un segundo expediente se rechaza en el servicio (la base también: prueba siguiente)
    with pytest.raises(services.OperacionNoValida, match="RD-10"):
        services.abrir_expediente(mascota)
    assert ExpedienteClinico.objects.filter(mascota=mascota).count() == 1


def test_TI01_la_base_rechaza_un_segundo_expediente(raza, cliente):
    """UQ_expediente_mascota. Va al final de su prueba: tras el error, SQL Server deja la transacción
    de la prueba sin poder consultar, así que no se hacen más consultas después."""
    mascota = Mascota.objects.create(cliente=cliente, raza=raza, nombre="Firulais", sexo=Sexo.MACHO)
    ExpedienteClinico.objects.create(mascota=mascota)
    with pytest.raises(IntegrityError), transaction.atomic():
        ExpedienteClinico.objects.create(mascota=mascota)


def test_si_el_expediente_falla_la_mascota_no_se_guarda(recepcion, raza, cliente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("no se pudo abrir el expediente")

    monkeypatch.setattr(services, "abrir_expediente", falla)
    with pytest.raises(RuntimeError):
        recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza))
    assert not Mascota.objects.exists()


def test_un_cliente_puede_tener_varias_mascotas_y_la_ficha_las_lista(recepcion, raza, cliente):
    recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza, nombre="Firulais"))
    recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza, nombre="Michi", sexo=Sexo.HEMBRA))
    assert cliente.mascotas.count() == 2
    assert ExpedienteClinico.objects.count() == 2
    ficha = recepcion.get(f"/clientes/{cliente.pk}/").content.decode()
    assert "Firulais" in ficha and "Michi" in ficha and "Nueva mascota" in ficha


def test_la_ficha_de_la_mascota_muestra_su_expediente_y_la_alerta_de_alergias(recepcion, raza, cliente):
    recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza))
    mascota = Mascota.objects.get()
    contenido = recepcion.get(f"/clientes/mascotas/{mascota.pk}/").content.decode()
    assert "Expediente clínico" in contenido
    assert "Alergias:" in contenido and "Penicilina" in contenido
    assert "Schnauzer" in contenido and "8.40 kg" in contenido


def test_las_razas_aparecen_agrupadas_por_especie(recepcion, raza, cliente):
    contenido = recepcion.get(f"/clientes/{cliente.pk}/mascotas/nueva/").content.decode()
    assert '<optgroup label="Perro">' in contenido and '<optgroup label="Gato">' in contenido


@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"nombre": ""}, "obligatorio"),
        ({"raza": ""}, "Elija la raza."),
        ({"sexo": ""}, "obligatorio"),
        ({"peso_actual": "0"}, "mayor que 0"),
        ({"peso_actual": "200"}, "hasta 150 kg"),
        ({"fecha_nacimiento": (timezone.localdate() + timedelta(days=1)).isoformat()}, "no puede ser futura"),
    ],
)
def test_alta_rechaza_datos_invalidos(recepcion, raza, cliente, cambio, mensaje):
    contenido = recepcion.post(
        f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza, **cambio)
    ).content.decode()
    assert mensaje in contenido
    assert not Mascota.objects.exists()
    assert not ExpedienteClinico.objects.exists()


def test_peso_y_nacimiento_son_opcionales(recepcion, raza, cliente):
    recepcion.post(
        f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza, peso_actual="", fecha_nacimiento="")
    )
    mascota = Mascota.objects.get()
    assert mascota.peso_actual is None and mascota.fecha_nacimiento is None
    assert mascota.estatus == EstatusMascota.ACTIVA


def test_edicion_cambia_datos_y_estatus_sin_tocar_el_expediente(recepcion, raza, cliente):
    recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza))
    mascota = Mascota.objects.get()
    contenido = recepcion.get(f"/clientes/mascotas/{mascota.pk}/editar/").content.decode()
    assert 'name="alergias"' not in contenido
    datos = _datos(raza, color="Negro", estatus=EstatusMascota.FALLECIDA)
    del datos["alergias"]
    recepcion.post(f"/clientes/mascotas/{mascota.pk}/editar/", datos)
    mascota.refresh_from_db()
    assert mascota.color == "Negro" and mascota.estatus == EstatusMascota.FALLECIDA
    assert ExpedienteClinico.objects.get(mascota=mascota).alergias == "Penicilina"


def test_a_un_cliente_dado_de_baja_no_se_le_registran_mascotas(recepcion, raza, cliente):
    Cliente.objects.filter(pk=cliente.pk).update(activo=False)
    assert recepcion.get(f"/clientes/{cliente.pk}/mascotas/nueva/").status_code == 404
    cliente.refresh_from_db()
    with pytest.raises(services.OperacionNoValida):
        services.registrar_mascota(cliente, None)


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ADMINISTRADOR])  # Estilista: test_estilista.py
def test_los_roles_de_consulta_ven_la_mascota_pero_no_la_registran(client, crear_usuario, raza, cliente, rol):
    mascota = Mascota.objects.create(cliente=cliente, raza=raza, nombre="Firulais", sexo=Sexo.MACHO)
    services.abrir_expediente(mascota)
    client.force_login(crear_usuario("usuario", rol=rol))
    contenido = client.get(f"/clientes/mascotas/{mascota.pk}/").content.decode()
    assert "Firulais" in contenido and "Editar" not in contenido
    assert client.get(f"/clientes/{cliente.pk}/mascotas/nueva/").status_code == 403
    assert client.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _datos(raza)).status_code == 403
    assert client.get(f"/clientes/mascotas/{mascota.pk}/editar/").status_code == 403
