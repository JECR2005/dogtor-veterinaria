"""S1-17 · Mensajes con las frases de las reglas (RI-08) y formato local de México (RI-13).

Criterio del plan: coinciden con el documento.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from django import forms
from django.template import Context, Template
from django.utils import formats, timezone, translation

from agenda import services
from catalogos.models import CategoriaServicio, Puesto
from seguridad.models import Rol
from tests import fabricas
from tests.fabricas import LUNES, en

pytestmark = pytest.mark.integracion


# --- RI-08 · Frases del documento (Tabla 4.29, TU-01, TU-03) ---------------------
def test_RI08_las_frases_de_las_reglas_son_las_del_documento():
    assert services.MENSAJE_FUERA_DE_HORARIO == "Fuera de horario laboral"
    assert services.MENSAJE_EMPALME == "Empalme de horario"


@pytest.mark.parametrize(
    "mensaje, indicacion",
    [
        ("Fuera de horario laboral", "Elija una hora dentro de la jornada del empleado"),
        ("Empalme de horario", "Elija otra hora u otro empleado, o reprograme la cita existente."),
        ("La mascota ya tiene una cita a esa hora: Baño a las 10:00 con Sofía", "reprograme la otra cita"),
        ("El cliente está dado de baja; no se le pueden agendar citas.", ""),
    ],
)
def test_RI08_cada_rechazo_dice_que_hacer(mensaje, indicacion):
    ayuda = services.que_hacer(mensaje)
    assert indicacion in ayuda if indicacion else ayuda == ""


@pytest.mark.django_db
def test_RI08_la_pantalla_muestra_la_frase_y_que_hacer(client, crear_usuario):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    mascota = fabricas.mascota()
    services.agendar(mascota, laura, consulta, en("10:00"))
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    datos = {"servicio": consulta.pk, "empleado": laura.pk, "fecha": LUNES.isoformat(), "hora": "10:15"}
    contenido = client.post(
        f"/agenda/nueva/?mascota={fabricas.mascota('Michi', 'Bruno').pk}", datos
    ).content.decode()
    assert "<strong>Empalme de horario</strong>" in contenido
    assert "No se guardó la cita." in contenido and "reprograme la cita existente" in contenido


@pytest.mark.django_db
def test_RI08_las_paginas_de_error_no_muestran_codigos_tecnicos(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    respuesta = client.get("/clientes/999999/")
    assert respuesta.status_code == 404
    contenido = respuesta.content.decode()
    assert "No encontramos lo que busca." in contenido and "Volver al inicio" in contenido
    assert "404" not in contenido and "Not Found" not in contenido


# --- RI-13 · Formato local de México -----------------------------------------------
def _formatear(plantilla, **valores):
    with translation.override("es-mx"):
        return Template("{% load formato %}" + plantilla).render(Context(valores))


def test_RI13_fecha_dia_mes_anio_y_hora_de_24_horas():
    momento = timezone.make_aware(datetime(2026, 11, 16, 18, 45))
    assert _formatear("{{ d }}", d=date(2026, 11, 16)) == "16/11/2026"
    assert _formatear("{{ m }}", m=momento) == "16/11/2026 18:45"
    assert _formatear("{{ m|time }}", m=momento) == "18:45"
    assert _formatear("{{ m|date:'SHORT_DATE_FORMAT' }}", m=momento) == "16/11/2026"


def test_RI13_importes_en_pesos_con_separador_de_miles():
    assert _formatear("{{ p|pesos }}", p=Decimal("1250")) == "$1,250.00"
    with translation.override("es-mx"):
        assert formats.number_format(Decimal("1250.5"), 2, use_l10n=True, force_grouping=True) == "1,250.50"


def test_RI13_el_formulario_acepta_la_fecha_como_la_escribe_la_recepcionista():
    with translation.override("es-mx"):
        campo = forms.DateField()
        assert campo.clean("16/11/2026") == date(2026, 11, 16)
        assert campo.clean("2026-11-16") == date(2026, 11, 16)
