"""S0-16 · El menú lateral respeta la Tabla 4.9 (acceso por rol) y el mínimo privilegio (RNF-01)."""

import pytest

from seguridad.menu import NIVEL_COMPLETO, NIVEL_CONSULTA, ROLES, nivel_de_acceso, opciones_para

pytestmark = pytest.mark.unidad


@pytest.mark.parametrize(
    ("rol", "cantidad"),
    [("Administrador", 12), ("Veterinario", 6), ("Estilista", 5), ("Recepcionista", 6)],
)
def test_S0_cada_rol_ve_solo_sus_opciones(rol, cantidad):
    # Apartado 4.4: entre cinco (Estilista) y doce (Administrador) opciones
    assert len(opciones_para(rol)) == cantidad


def test_S0_todos_los_roles_tienen_inicio_y_mi_cuenta():
    for rol in ROLES:
        claves = [o["clave"] for o in opciones_para(rol)]
        assert claves[0] == "inicio"
        assert claves[-1] == "cuenta"


@pytest.mark.parametrize(
    ("rol", "opcion", "esperado"),
    [
        ("Recepcionista", "ventas", NIVEL_COMPLETO),
        ("Recepcionista", "inventario", None),
        ("Recepcionista", "consulta", None),
        ("Estilista", "consulta", None),
        ("Estilista", "estetica", NIVEL_COMPLETO),
        ("Veterinario", "consulta", NIVEL_COMPLETO),
        ("Veterinario", "agenda", NIVEL_CONSULTA),
        ("Veterinario", "bitacora", None),
        ("Administrador", "bitacora", NIVEL_COMPLETO),
        ("Administrador", "consulta", NIVEL_CONSULTA),
    ],
)
def test_S0_nivel_de_acceso_segun_tabla_4_9(rol, opcion, esperado):
    assert nivel_de_acceso(rol, opcion) == esperado


def test_S0_opcion_desconocida_es_un_error():
    with pytest.raises(KeyError):
        nivel_de_acceso("Administrador", "hospitalizacion")
