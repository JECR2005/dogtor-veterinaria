"""S5-24 · Recomendaciones de QA: nombres sin números y la letra Ñ de punta a punta.

- Alta de cliente, mascota y empleado por las pantallas: un nombre con números no se guarda y el mensaje dice
  por qué; un peso escrito con «e» tampoco.
- La Ñ se guarda tal cual en SQL Server (NVARCHAR), se busca sin distinguir mayúsculas («PEÑA» = «peña») y
  sigue siendo una letra distinta de la N, como en español (intercalación Modern_Spanish_CI_AI): «pena» no
  encuentra a «Peña». También sale bien en la ficha y en un PDF.
"""

from io import BytesIO

import pytest
from pypdf import PdfReader

from catalogos.campos import MENSAJE_EXPONENTE
from catalogos.models import Cliente, Empleado, Especie, Mascota, PreferenciaContacto, Puesto, Raza, Sexo
from catalogos.services import buscar_clientes
from reportes.services import pdf_desde_html
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CLIENTE = {
    "nombre": "Iñaki",
    "apellido_paterno": "Peña",
    "apellido_materno": "Muñoz",
    "telefono": "833 555 0177",
    "correo": "",
    "direccion": "Calle Españita 12",
    "preferencia_contacto": PreferenciaContacto.WHATSAPP,
    "rfc": "",
    "razon_social_fiscal": "",
    "regimen_fiscal": "",
    "cp_fiscal": "",
    "acepto_aviso_privacidad": "on",
}


@pytest.fixture
def recepcion(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    return client


@pytest.fixture
def raza():
    perro, _ = Especie.objects.get_or_create(nombre="Perro")
    return Raza.objects.get_or_create(especie=perro, nombre="Mestizo")[0]


def _mascota(raza, **cambios):
    return {
        "nombre": "Ñoño",
        "raza": raza.pk,
        "sexo": Sexo.MACHO,
        "fecha_nacimiento": "",
        "peso_actual": "8.5",
        "color": "Café",
        "alergias": "",
        "antecedentes": "",
        **cambios,
    }


def _texto(respuesta):
    return respuesta.content.decode()


def test_S5_24_un_cliente_con_numeros_en_el_nombre_no_se_guarda(recepcion):
    for campo, valor in [("nombre", "Iñaki2"), ("apellido_paterno", "Peña 3"), ("apellido_materno", "M4")]:
        respuesta = recepcion.post("/clientes/nuevo/", {**CLIENTE, campo: valor})
        assert respuesta.status_code == 200 and "No lleva números." in _texto(respuesta), campo
    assert not Cliente.objects.filter(telefono="8335550177").exists()


def test_S5_24_una_mascota_con_numeros_en_el_nombre_o_un_peso_con_e_no_se_guarda(recepcion, raza):
    recepcion.post("/clientes/nuevo/", CLIENTE)
    cliente = Cliente.objects.get(telefono="8335550177")
    url = f"/clientes/{cliente.pk}/mascotas/nueva/"
    assert "No lleva números." in _texto(recepcion.post(url, _mascota(raza, nombre="Firulais 2")))
    assert MENSAJE_EXPONENTE in _texto(recepcion.post(url, _mascota(raza, peso_actual="8e1")))
    assert not Mascota.objects.filter(cliente=cliente).exists()


def test_S5_24_un_empleado_con_numeros_en_el_nombre_no_se_guarda(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    datos = {
        "empleado-nombre": "Laura3",
        "empleado-apellidos": "Ñúñez Ficticia",
        "empleado-puesto": Puesto.RECEPCIONISTA,
        "empleado-cedula_profesional": "",
        "empleado-telefono": "",
        "empleado-fecha_ingreso": "2026-11-02",
    }
    contenido = _texto(client.post("/administracion/empleados/nuevo/", datos))
    assert "No lleva números." in contenido
    assert not Empleado.objects.filter(apellidos="Ñúñez Ficticia").exists()


def test_S5_24_la_enie_se_guarda_se_busca_y_se_muestra_tal_cual(recepcion, raza):
    respuesta = recepcion.post("/clientes/nuevo/", CLIENTE, follow=True)
    cliente = Cliente.objects.get(telefono="8335550177")
    assert (cliente.nombre, cliente.apellido_paterno, cliente.apellido_materno) == ("Iñaki", "Peña", "Muñoz")
    assert cliente.direccion == "Calle Españita 12"
    assert "Iñaki Peña" in _texto(respuesta) and "Muñoz" in _texto(respuesta)

    respuesta = recepcion.post(f"/clientes/{cliente.pk}/mascotas/nueva/", _mascota(raza), follow=True)
    assert Mascota.objects.get(cliente=cliente).nombre == "Ñoño" and "Ñoño" in _texto(respuesta)

    # Búsqueda sin distinguir mayúsculas ni acentos; la Ñ es su propia letra
    for texto in ["peña", "PEÑA", "Peña", "muñoz", "MUÑOZ", "iñaki", "IÑAKI", "ñoño", "ÑOÑO", "peña muñoz"]:
        assert list(buscar_clientes(texto)) == [cliente], texto
    for texto in ["pena", "munoz", "inaki", "nono"]:
        assert cliente not in list(buscar_clientes(texto)), texto
    assert "Iñaki" in _texto(recepcion.get("/clientes/", {"q": "PEÑA"}))


def test_S5_24_la_enie_sale_bien_en_un_pdf():
    contenido = pdf_desde_html("<html><body><p>Cliente: Iñaki Peña Muñoz · Mascota: Ñoño</p></body></html>")
    texto = PdfReader(BytesIO(contenido)).pages[0].extract_text()
    assert "Iñaki Peña Muñoz" in texto and "Ñoño" in texto
