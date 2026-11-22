"""S5-24 · Recomendaciones de QA: números sin la letra «e» y nombres solo con letras.

- Ningún campo decimal de los formularios acepta notación científica («1e2» = 100); los enteros ya la
  rechazan.
- En pantalla, static/js/numeros.js impide escribir o pegar «e», «E», «+» y «-» en los campos numéricos. Es
  seguro bloquear el signo menos porque ningún campo numérico admite negativos (todos tienen min ≥ 0).
- Nombres y apellidos de clientes y empleados, y el nombre de la mascota: letras (con acentos, ü y ñ),
  espacios, apóstrofo, guion y punto; sin números; al menos 2 letras.
"""

import inspect
import re
from pathlib import Path

import pytest
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from agenda import forms as agenda_forms
from catalogos import forms as catalogos_forms
from catalogos.campos import MENSAJE_EXPONENTE, DecimalSinExponente, validar_nombre
from clinico import forms as clinico_forms
from inventario import forms as inventario_forms
from ventas import forms as ventas_forms
from ventas.forms import PagoForm

pytestmark = pytest.mark.unidad

MODULOS = [agenda_forms, catalogos_forms, clinico_forms, inventario_forms, ventas_forms]


def _formularios():
    for modulo in MODULOS:
        for nombre, clase in inspect.getmembers(modulo, inspect.isclass):
            if issubclass(clase, forms.BaseForm) and clase.__module__ == modulo.__name__:
                yield f"{modulo.__name__}.{nombre}", clase


# --- La letra «e» en los números -------------------------------------------------------------------
@pytest.mark.parametrize("texto", ["1e2", "2E-1", "1e5", "3.5e1", "E2"])
def test_S5_24_un_decimal_con_e_se_rechaza_con_un_mensaje_claro(texto):
    with pytest.raises(ValidationError) as error:
        DecimalSinExponente(max_digits=10, decimal_places=2).clean(texto)
    assert error.value.messages == [MENSAJE_EXPONENTE]


@pytest.mark.parametrize(("texto", "valor"), [("12.50", "12.50"), ("3", "3"), (" 150 ", "150")])
def test_S5_24_un_decimal_normal_se_acepta(texto, valor):
    assert str(DecimalSinExponente(max_digits=10, decimal_places=2).clean(texto)) == valor


def test_S5_24_un_entero_con_e_tambien_se_rechaza():
    with pytest.raises(ValidationError):
        forms.IntegerField(min_value=0).clean("1e2")


def test_S5_24_todos_los_campos_decimales_de_los_formularios_rechazan_la_e():
    sin_proteccion = [
        f"{clase}.{campo}"
        for clase, formulario in _formularios()
        for campo, definicion in formulario.base_fields.items()
        if isinstance(definicion, forms.DecimalField) and not isinstance(definicion, DecimalSinExponente)
    ]
    assert not sin_proteccion, sin_proteccion


def test_S5_24_ningun_campo_numerico_admite_negativos_asi_que_bloquear_el_signo_menos_es_seguro():
    revisados, sin_minimo = 0, []
    for clase, formulario in _formularios():
        for campo, definicion in formulario.base_fields.items():
            if isinstance(definicion.widget, forms.NumberInput):
                revisados += 1
                minimo = definicion.widget.attrs.get("min")
                if minimo is None or float(minimo) < 0:
                    sin_minimo.append(f"{clase}.{campo}")
    assert revisados >= 15 and not sin_minimo, sin_minimo


def test_S5_24_el_cobro_rechaza_un_monto_con_e():
    formulario = PagoForm(data={"metodo": "Efectivo", "recibido": "1e3"})
    assert not formulario.is_valid()
    assert formulario.errors["recibido"] == [MENSAJE_EXPONENTE]


def test_S5_24_todas_las_pantallas_cargan_el_bloqueo_de_la_e():
    base = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(encoding="utf-8")
    assert "js/numeros.js" in base
    script = (Path(settings.BASE_DIR) / "static" / "js" / "numeros.js").read_text(encoding="utf-8")
    assert '["e", "E", "+", "-"]' in script
    assert 'type === "number"' in script and '"paste"' in script and '"keydown"' in script


# --- Nombres sin números ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("texto", "limpio"),
    [
        ("José", "José"),
        ("  María   José ", "María José"),
        ("Peña Muñoz", "Peña Muñoz"),
        ("Iñaki", "Iñaki"),
        ("O'Connor", "O'Connor"),
        ("Ana-Lucía", "Ana-Lucía"),
        ("Ma. Elena", "Ma. Elena"),
        ("Müller", "Müller"),
        ("Ñoño", "Ñoño"),
        ("Sr. Bigotes", "Sr. Bigotes"),
    ],
)
def test_S5_24_nombres_validos(texto, limpio):
    assert validar_nombre(texto) == limpio


@pytest.mark.parametrize(
    "texto", ["Ana2", "Firulais 2", "R2D2", "3ro", "Juan$", "Ana_María", "<script>", "Pedro@", "-Ana", ".Max"]
)
def test_S5_24_nombres_con_numeros_o_simbolos_se_rechazan(texto):
    with pytest.raises(ValidationError) as error:
        validar_nombre(texto, "el nombre")
    assert error.value.code == "caracteres"
    assert "solo con letras" in error.value.messages[0] and "No lleva números." in error.value.messages[0]


@pytest.mark.parametrize("texto", ["A", "Ñ.", "J-"])
def test_S5_24_un_nombre_necesita_al_menos_2_letras(texto):
    with pytest.raises(ValidationError) as error:
        validar_nombre(texto, "el nombre")
    assert error.value.code == "letras"


def test_S5_24_el_apellido_materno_puede_quedar_vacio_pero_no_con_numeros():
    assert validar_nombre("   ", obligatorio=False) is None
    with pytest.raises(ValidationError):
        validar_nombre("López 2", obligatorio=False)


def test_S5_24_los_formularios_de_personas_y_mascotas_usan_la_validacion():
    fuente = inspect.getsource(catalogos_forms)
    for clase, campos in {
        "ClienteForm": ["nombre", "apellido_paterno", "apellido_materno"],
        "MascotaForm": ["nombre"],
        "EmpleadoForm": ["nombre", "apellidos"],
    }.items():
        cuerpo = inspect.getsource(getattr(catalogos_forms, clase))
        for campo in campos:
            metodo = re.search(rf"def clean_{campo}\(self\):\n(.*?)(?=\n    def |\Z)", cuerpo, re.S)
            assert metodo and "validar_nombre(" in metodo.group(1), f"{clase}.clean_{campo}"
    assert "from .campos import DecimalSinExponente, validar_nombre" in fuente
