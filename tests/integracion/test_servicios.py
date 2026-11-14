"""S1-11 · UI-04 Catálogo de servicios (RF-04, RD-04). Solo el Administrador."""

import pytest
from django.db import IntegrityError, transaction

from catalogos.models import CategoriaServicio, PuestoRequerido, Servicio
from seguridad.models import Rol

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

RUTA = "/administracion/servicios/"


@pytest.fixture
def admin(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    return client


def _servicio(nombre, categoria=CategoriaServicio.CONSULTA, precio="400.00", duracion=30, activo=True):
    return Servicio.objects.create(
        nombre=nombre,
        categoria=categoria,
        precio=precio,
        duracion_min=duracion,
        puesto_requerido=Servicio.puesto_para(categoria),
        agendable=categoria != CategoriaServicio.APLICACION,
        activo=activo,
    )


def _datos(**cambios):
    datos = {
        "nombre": "Corte de uñas",
        "categoria": CategoriaServicio.ESTETICA,
        "precio": "150.00",
        "duracion_min": "20",
        "agendable": "on",
    }
    datos.update(cambios)
    return {k: v for k, v in datos.items() if v is not None}


def test_la_lista_muestra_precio_en_pesos_y_duracion(admin):
    _servicio("Cirugía menor", CategoriaServicio.PROCEDIMIENTO_MENOR, "1250.00", 90)
    contenido = admin.get(RUTA).content.decode()
    assert "Cirugía menor" in contenido and "$1,250.00" in contenido and "1 h 30 min" in contenido
    assert "Catálogo de servicios" in contenido and "Empleados y usuarios" in contenido  # pestañas


def test_filtro_por_categoria_y_por_activos(admin):
    _servicio("Consulta general")
    _servicio("Baño", CategoriaServicio.ESTETICA, "350.00", 60)
    _servicio("Baño medicado", CategoriaServicio.ESTETICA, "420.00", 60, activo=False)
    contenido = admin.get(RUTA, {"categoria": CategoriaServicio.ESTETICA}).content.decode()
    assert "Baño" in contenido and "Consulta general" not in contenido and "Baño medicado" not in contenido
    contenido = admin.get(RUTA, {"categoria": CategoriaServicio.ESTETICA, "inactivos": "1"}).content.decode()
    assert "Baño medicado" in contenido and "Inactivo" in contenido


def test_alta_de_estetica_la_presta_un_estilista(admin):
    respuesta = admin.post(f"{RUTA}nuevo/", _datos(), follow=True)
    assert "registrado" in respuesta.content.decode()
    servicio = Servicio.objects.get(nombre="Corte de uñas")
    assert servicio.puesto_requerido == PuestoRequerido.ESTILISTA
    assert servicio.agendable and servicio.activo


def test_alta_de_aplicacion_no_se_agenda_aunque_se_marque(admin):
    admin.post(f"{RUTA}nuevo/", _datos(nombre="Aplicación de vacuna", categoria=CategoriaServicio.APLICACION))
    servicio = Servicio.objects.get(nombre="Aplicación de vacuna")
    assert servicio.puesto_requerido == PuestoRequerido.VETERINARIO
    assert not servicio.agendable


@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"nombre": ""}, "obligatorio"),
        ({"categoria": ""}, "obligatorio"),
        ({"precio": "-1"}, "no puede ser negativo"),
        ({"precio": "150000"}, "mayor a $99,999.99"),
        ({"duracion_min": "0"}, "de 5 a 480 minutos"),
        ({"duracion_min": "22"}, "múltiplos de 5"),
        ({"duracion_min": "600"}, "de 5 a 480 minutos"),
    ],
)
def test_alta_rechaza_datos_invalidos(admin, cambio, mensaje):
    contenido = admin.post(f"{RUTA}nuevo/", _datos(**cambio)).content.decode()
    assert mensaje in contenido
    assert not Servicio.objects.exists()


def test_no_se_repite_el_nombre_de_un_servicio_activo(admin):
    _servicio("Consulta general")
    contenido = admin.post(f"{RUTA}nuevo/", _datos(nombre="consulta  GENERAL")).content.decode()
    assert "Ya existe un servicio activo con ese nombre." in contenido


def test_editar_precio_y_desactivar(admin):
    servicio = _servicio("Consulta general")
    datos = _datos(
        nombre="Consulta general", categoria=CategoriaServicio.CONSULTA, precio="450.00", duracion_min="30"
    )
    admin.post(f"{RUTA}{servicio.pk}/", datos, follow=True)  # sin «activo»: queda inactivo
    servicio.refresh_from_db()
    assert str(servicio.precio) == "450.00" and not servicio.activo
    assert "Consulta general" not in admin.get(RUTA).content.decode()


def test_cambiar_de_categoria_cambia_quien_lo_presta(admin):
    servicio = _servicio("Revisión de piel")
    datos = _datos(nombre="Revisión de piel", categoria=CategoriaServicio.ESTETICA, activo="on")
    admin.post(f"{RUTA}{servicio.pk}/", datos)
    servicio.refresh_from_db()
    assert servicio.puesto_requerido == PuestoRequerido.ESTILISTA


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA])
def test_solo_el_administrador_entra_al_catalogo(client, crear_usuario, rol):
    servicio = _servicio("Consulta general")
    client.force_login(crear_usuario("usuario", rol=rol))
    assert client.get(RUTA).status_code == 403
    assert client.post(f"{RUTA}nuevo/", _datos()).status_code == 403
    assert client.post(f"{RUTA}{servicio.pk}/", _datos()).status_code == 403


def test_RD04_la_base_rechaza_estetica_prestada_por_veterinario():
    """Al final de la prueba: tras el error, SQL Server deja la transacción sin poder consultar."""
    with pytest.raises(IntegrityError), transaction.atomic():
        Servicio.objects.create(
            nombre="Baño",
            categoria=CategoriaServicio.ESTETICA,
            precio="350.00",
            duracion_min=60,
            puesto_requerido=PuestoRequerido.VETERINARIO,
        )
