"""S0-13 · Usuario propio (Tabla 3.38): hash de contraseña, rol obligatorio y cuenta inicial."""

from datetime import date

import pytest

from catalogos.models import Empleado, Puesto
from seguridad.models import Rol, Usuario

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


def _empleado(puesto=Puesto.RECEPCIONISTA):
    return Empleado.objects.create(
        nombre="Prueba", apellidos="Usuario", puesto=puesto, fecha_ingreso=date.today()
    )


def test_S0_la_contrasena_nunca_se_guarda_en_texto_plano():  # RNF-01
    usuario = Usuario.objects.create_user(
        "recepcion1", "Clave-Segura-2026", empleado=_empleado(), rol=Rol.RECEPCIONISTA
    )
    assert usuario.password != "Clave-Segura-2026"
    assert usuario.check_password("Clave-Segura-2026")


def test_S0_no_se_crea_una_cuenta_sin_rol():  # RF-03
    with pytest.raises(ValueError):
        Usuario.objects.create_user("sinrol", "Clave-Segura-2026", empleado=_empleado())


def test_S0_createsuperuser_crea_al_empleado_administrador():  # D-05
    admin = Usuario.objects.create_superuser("admin", "Clave-Segura-2026")
    assert admin.rol == Rol.ADMINISTRADOR
    assert admin.empleado.puesto == Puesto.ADMINISTRADOR


def test_S0_tiene_permiso_aplica_minimo_privilegio():  # RNF-01, Tabla 4.9
    usuario = Usuario.objects.create_user(
        "recepcion2", "Clave-Segura-2026", empleado=_empleado(), rol=Rol.RECEPCIONISTA
    )
    assert usuario.tiene_permiso("ventas", "completo")
    assert not usuario.tiene_permiso("inventario")
    usuario.intentos_fallidos = 5  # cuenta bloqueada
    assert not usuario.tiene_permiso("ventas")
