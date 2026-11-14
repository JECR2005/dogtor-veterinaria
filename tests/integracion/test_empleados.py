"""S1-10 · UI-03 Empleados y usuarios: puesto, horario semanal, cédula y cuenta con rol (RF-03, RD-01).

Criterio del plan: pasa TU-05 (sin cédula no se guarda un veterinario; con cédula sí).
"""

from datetime import time

import pytest

from catalogos.models import Empleado, HorarioLaboral, Puesto
from seguridad import services as seguridad
from seguridad.models import Rol, Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

CLAVE = "Bata-Blanca-2026"


@pytest.fixture
def admin(client, crear_usuario):
    usuario = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    client.force_login(usuario)
    return usuario


def _horario(dias=range(1, 7), entrada="09:00", salida="19:00"):
    datos = {}
    for dia in range(1, 7):
        datos[f"horario-entrada_{dia}"] = entrada if dia in dias else ""
        datos[f"horario-salida_{dia}"] = salida if dia in dias else ""
    return datos


def _datos(**cambios):
    datos = {
        "empleado-nombre": "Laura",
        "empleado-apellidos": "Ficticia Pérez",
        "empleado-puesto": Puesto.VETERINARIO,
        "empleado-cedula_profesional": "12345678",
        "empleado-telefono": "833 555 1234",
        "empleado-fecha_ingreso": "2026-11-02",
        "cuenta-crear": "on",
        "cuenta-nombre_usuario": "laura",
        "cuenta-rol": Rol.VETERINARIO,
        "cuenta-contrasena": CLAVE,
        "cuenta-confirmacion": CLAVE,
        **_horario(dias=range(1, 6)),
    }
    datos.update(cambios)
    return {k: v for k, v in datos.items() if v is not None}


def test_la_lista_muestra_puesto_horario_y_cuenta(client, admin):
    contenido = client.get("/administracion/empleados/").content.decode()
    assert "Empleados y usuarios" in contenido
    assert "admin · Administrador" in contenido
    assert 'href="/administracion/empleados/"' in contenido  # el menú «Administración» lleva aquí


# --- TU-05 desde la pantalla ----------------------------------------------------
def test_TU05_veterinario_sin_cedula_no_se_guarda(client, admin):
    contenido = client.post(
        "/administracion/empleados/nuevo/", _datos(**{"empleado-cedula_profesional": ""})
    ).content.decode()
    assert Empleado.MENSAJE_CEDULA in contenido
    assert not Empleado.objects.filter(nombre="Laura").exists()
    assert not Usuario.objects.filter(nombre_usuario="laura").exists()


def test_TU05_veterinario_con_cedula_se_guarda_con_horario_y_cuenta(client, admin):
    respuesta = client.post("/administracion/empleados/nuevo/", _datos(), follow=True)
    assert "registrado" in respuesta.content.decode()
    laura = Empleado.objects.get(nombre="Laura")
    assert laura.cedula_profesional == "12345678" and laura.telefono == "8335551234"
    assert sorted(laura.horarios.values_list("dia_semana", flat=True)) == [1, 2, 3, 4, 5]
    assert laura.horarios.get(dia_semana=1).hora_entrada == time(9, 0)
    cuenta = Usuario.objects.get(nombre_usuario="laura")
    assert cuenta.empleado == laura and cuenta.rol == Rol.VETERINARIO
    assert seguridad.autenticar("laura", CLAVE).aceptado


def test_empleado_sin_cuenta(client, admin):
    datos = _datos(
        **{"empleado-puesto": Puesto.RECEPCIONISTA, "empleado-cedula_profesional": "", "cuenta-crear": None}
    )
    client.post("/administracion/empleados/nuevo/", datos)
    laura = Empleado.objects.get(nombre="Laura")
    assert not Usuario.objects.filter(empleado=laura).exists()


# --- Cuenta (RF-03: no se crea una cuenta sin rol) -----------------------------
@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"cuenta-rol": ""}, "la cuenta necesita un rol"),
        ({"cuenta-nombre_usuario": "admin"}, "ya existe"),
        ({"cuenta-nombre_usuario": "Laura Pérez"}, "minúsculas"),
        ({"cuenta-contrasena": ""}, "contraseña inicial"),
        ({"cuenta-confirmacion": "otra"}, "no coinciden"),
    ],
)
def test_la_cuenta_se_valida(client, admin, cambio, mensaje):
    contenido = client.post("/administracion/empleados/nuevo/", _datos(**cambio)).content.decode()
    assert mensaje in contenido
    assert not Empleado.objects.filter(nombre="Laura").exists()


# --- Horario semanal ------------------------------------------------------------
@pytest.mark.parametrize(
    "horario, mensaje",
    [
        (_horario(entrada="14:00", salida="10:00"), "la salida debe ser después de la entrada"),
        (_horario(entrada="08:00", salida="12:00"), "entre 09:00 y 19:00"),
        (_horario(entrada="10:00", salida="20:00"), "entre 09:00 y 19:00"),
        ({**_horario(), "horario-salida_3": ""}, "capture la hora de entrada y la de salida"),
        (_horario(dias=[]), "al menos un día de horario"),
    ],
)
def test_el_horario_se_valida(client, admin, horario, mensaje):
    contenido = client.post("/administracion/empleados/nuevo/", _datos(**horario)).content.decode()
    assert mensaje in contenido
    assert not Empleado.objects.filter(nombre="Laura").exists()


def test_recepcionista_puede_quedar_sin_horario(client, admin):
    datos = _datos(
        **_horario(dias=[]),
        **{
            "empleado-puesto": Puesto.RECEPCIONISTA,
            "empleado-cedula_profesional": "",
            "cuenta-rol": Rol.RECEPCIONISTA,
        },
    )
    client.post("/administracion/empleados/nuevo/", datos)
    assert Empleado.objects.get(nombre="Laura").horarios.count() == 0


# --- Edición ----------------------------------------------------------------------
def test_editar_reemplaza_el_horario_y_cambia_el_rol_y_la_contrasena(client, admin):
    client.post("/administracion/empleados/nuevo/", _datos())
    laura = Empleado.objects.get(nombre="Laura")
    datos = _datos(
        **_horario(dias=[6], entrada="10:00", salida="14:00"),
        **{
            "empleado-activo": "on",
            "cuenta-crear": None,
            "cuenta-nombre_usuario": None,
            "cuenta-activa": "on",
            "cuenta-rol": Rol.ESTILISTA,
            "cuenta-contrasena": "Nueva-Bata-2026",
            "cuenta-confirmacion": "Nueva-Bata-2026",
        },
    )
    client.post(f"/administracion/empleados/{laura.pk}/", datos)
    horarios = list(HorarioLaboral.objects.filter(empleado=laura).values_list("dia_semana", "hora_entrada"))
    assert horarios == [(6, time(10, 0))]
    cuenta = Usuario.objects.get(nombre_usuario="laura")
    assert cuenta.rol == Rol.ESTILISTA
    assert seguridad.autenticar("laura", "Nueva-Bata-2026").aceptado
    assert not seguridad.autenticar("laura", CLAVE).aceptado


def test_un_empleado_inactivo_ya_no_puede_entrar(client, admin):
    client.post("/administracion/empleados/nuevo/", _datos())
    laura = Empleado.objects.get(nombre="Laura")
    datos = _datos(**{"cuenta-crear": None, "cuenta-nombre_usuario": None, "cuenta-activa": "on"})
    client.post(f"/administracion/empleados/{laura.pk}/", datos)  # sin «empleado-activo»: inactivo
    laura.refresh_from_db()
    assert not laura.activo
    assert not Usuario.objects.get(nombre_usuario="laura").activo
    assert not seguridad.autenticar("laura", CLAVE).aceptado


def test_el_administrador_no_puede_quitarse_su_propio_acceso(client, admin):
    datos = _datos(
        **_horario(dias=[]),
        **{
            "empleado-nombre": "Admin",
            "empleado-puesto": Puesto.ADMINISTRADOR,
            "empleado-cedula_profesional": "",
            "cuenta-crear": None,
            "cuenta-nombre_usuario": None,
            "cuenta-rol": Rol.RECEPCIONISTA,
        },
    )  # sin «empleado-activo» ni «cuenta-activa»
    client.post(f"/administracion/empleados/{admin.empleado.pk}/", datos)
    admin.refresh_from_db()
    admin.empleado.refresh_from_db()
    assert admin.activo and admin.rol == Rol.ADMINISTRADOR and admin.empleado.activo
    assert client.get("/administracion/empleados/").status_code == 200


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA])
def test_solo_el_administrador_entra_a_empleados(client, crear_usuario, rol):
    usuario = crear_usuario("usuario", rol=rol)
    client.force_login(usuario)
    assert client.get("/administracion/empleados/").status_code == 403
    assert client.post("/administracion/empleados/nuevo/", _datos()).status_code == 403
    assert client.get(f"/administracion/empleados/{usuario.empleado.pk}/").status_code == 403
