"""Escenarios de aceptación de P3 automatizados (TA-04, TA-05 y TA-06, Tabla 4.14).

Recorren por las pantallas, paso a paso, el guion docs/gestion/guion_aceptacion_P3.md con los datos ficticios
de `cargar_datos_prueba` (Max, Michi, Rocky y Canela), como lo harían el Veterinario, la Recepcionista y el
Estilista con el navegador, sobre la base real de pruebas.

Sirven de regresión: si un cambio rompe el flujo del guion, la CI lo detecta antes de la evaluación.
NO sustituyen la aceptación: la evalúa el personal de la clínica, sin ayuda del equipo de desarrollo, con una
calificación de al menos 4 de 5 (apartado 4.5.2.3, Tabla 3.20).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import Mascota, Producto
from clinico.models import Consulta, RegistroEstetica
from inventario.models import Lote, MovimientoInventario
from recordatorios.models import EstadoRecordatorio, Recordatorio
from seguridad.models import Usuario

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def datos():
    """Lo que el observador prepara: datos ficticios limpios (python manage.py cargar_datos_prueba)."""
    call_command("cargar_datos_prueba", mascotas=0)


def _entrar(client, cuenta):
    client.force_login(Usuario.objects.get(nombre_usuario=cuenta))


def _texto(respuesta):
    return respuesta.content.decode()


def _existencias(numero_lote):
    return Lote.objects.get(numero_lote=numero_lote).cantidad_disponible


def _receta(producto, dosis, frecuencia, dias, total=4):
    datos = {
        "indicaciones_generales": "Reposo y revisión en 7 días",
        "medicamentos-TOTAL_FORMS": str(total),
        "medicamentos-INITIAL_FORMS": "0",
        "medicamentos-MIN_NUM_FORMS": "4",
        "medicamentos-MAX_NUM_FORMS": "12",
    }
    for i in range(total):
        fila = (producto.pk, dosis, frecuencia, dias) if i == 0 else ("", "", "", "")
        for campo, valor in zip(("producto", "dosis", "frecuencia", "duracion_dias"), fila, strict=True):
            datos[f"medicamentos-{i}-{campo}"] = valor
        datos[f"medicamentos-{i}-indicaciones"] = ""
    return datos


def test_TA04_firmar_una_consulta_con_una_vacuna_y_una_receta(client, datos):
    max_ = Mascota.objects.get(nombre="Max", cliente__telefono="8339990001")
    cita = Cita.objects.get(mascota=max_, estado=EstadoCita.PROGRAMADA)
    vacuna = Producto.objects.get(codigo="VAC-002")
    amoxicilina = Producto.objects.get(codigo="MED-001")
    assert (_existencias("VAC-002-A"), _existencias("MED-001-A"), _existencias("MED-001-B")) == (18, 20, 40)
    _entrar(client, "veterinario")

    # 1. Consultas del día: Max a las 10:00 con su alerta de alergias
    dia = _texto(client.get("/clinica/"))
    assert "Mis consultas de hoy" in dia and "Max" in dia and "Alergias" in dia
    assert f"/clinica/citas/{cita.pk}/atender/" in dia

    # 2. Atender: la alerta roja de Penicilina; abrir con síntomas y peso
    atender = _texto(client.get(f"/clinica/citas/{cita.pk}/atender/"))
    assert 'data-alerta="alergias"' in atender and "Penicilina" in atender
    datos_consulta = {"sintomas": "Revisión anual y vacuna antirrábica", "peso_kg": "29.10"}
    respuesta = client.post(f"/clinica/citas/{cita.pk}/atender/", datos_consulta, follow=True)
    assert "Consulta de Max abierta." in _texto(respuesta)
    consulta = Consulta.objects.get(cita=cita)
    url = f"/clinica/consultas/{consulta.pk}/"

    # 3. Vacuna antirrábica: se toma del lote que caduca primero y baja una sola vez
    assert "se tomará del lote VAC-002-A" in _texto(client.get(url))
    aplicacion = {
        "producto": vacuna.pk,
        "cantidad": "1",
        "dosis": "1 mL subcutánea",
        "proxima_fecha": (HOY + timedelta(days=365)).isoformat(),
    }
    respuesta = client.post(f"{url}aplicar/", aplicacion, follow=True)
    assert "Aplicación registrada: Vacuna antirrábica, lote VAC-002-A." in _texto(respuesta)
    assert _existencias("VAC-002-A") == Decimal("17")

    # 4. Receta de amoxicilina: folio, y las existencias no cambian
    respuesta = client.post(
        f"{url}receta/", _receta(amoxicilina, "1 tableta", "Cada 12 horas", 7), follow=True
    )
    folio = f"R-{HOY:%Y}-00001"
    assert f"Receta {folio} emitida." in _texto(respuesta)
    assert (_existencias("MED-001-A"), _existencias("MED-001-B")) == (20, 40)

    # 5. Sin diagnóstico no se firma
    assert "Antes de firmar capture: diagnóstico." in _texto(client.get(f"{url}firmar/"))

    # 6. Capturar el diagnóstico y firmar
    completa = {**datos_consulta, "temperatura_c": "38.6", "diagnostico": "Sano", "tratamiento": "Ninguno"}
    assert "Consulta guardada." in _texto(client.post(url, {**completa, "observaciones": ""}, follow=True))
    respuesta = client.post(f"{url}firmar/", follow=True)
    assert "Consulta firmada. La cita quedó completada y el peso de Max se actualizó a 29.10 kg." in _texto(
        respuesta
    )
    assert "Es de solo lectura (RD-07)" in _texto(respuesta)
    cita.refresh_from_db()
    max_.refresh_from_db()
    assert cita.estado == EstadoCita.COMPLETADA and max_.peso_actual == Decimal("29.10")

    # 7. El lote bajó una sola vez y la receta no movió nada
    assert _existencias("VAC-002-A") == Decimal("17")
    referencias = MovimientoInventario.objects.filter(referencia=f"Consulta {consulta.pk}")
    assert list(referencias.values_list("tipo", "cantidad")) == [("Aplicación", Decimal("-1"))]
    historial = _texto(client.get(f"/clinica/mascotas/{max_.pk}/historial/"))
    assert f"Receta {folio}" in historial and "Vacuna antirrábica" in historial

    # 8. Solo firma quien tiene cédula: el Administrador consulta pero no firma
    _entrar(client, "administrador")
    assert "Firmar consulta" not in _texto(client.get(url))
    assert client.post(f"{url}firmar/").status_code == 403


def test_TA05_revisar_la_lista_de_recordatorios(client, datos):
    _entrar(client, "recepcion")
    manana_hay_servicio = (HOY + timedelta(days=1)).isoweekday() != 7
    esperados = 2 if manana_hay_servicio else 1  # Michi y, si mañana no es domingo, la cita de Canela

    # 1. El Inicio dice cuántos hay
    assert f'data-aviso="recordatorios">{esperados}<' in _texto(client.get("/"))

    # 2. Michi aparece 3 días antes de su dosis, con el teléfono de Jorge; Rocky (4 días) todavía no
    lista = _texto(client.get("/recordatorios/"))
    assert "Jorge Salas" in lista and "Michi" in lista and "Próxima dosis: Vacuna antirrábica" in lista
    assert "en 3 días" in lista and "tel:+528339990002" in lista and "Llamar" in lista
    assert "Rocky" not in lista
    if manana_hay_servicio:
        assert "Canela" in lista and "Cita: Corte y estética a las 11:00" in lista
        assert "mailto:ana.vega@example.com" in lista

    # 3. Marcar a Michi como Contactado: sale de los pendientes
    michi = Recordatorio.objects.get(aplicacion__consulta__expediente__mascota__nombre="Michi")
    respuesta = client.post(f"/recordatorios/{michi.pk}/resultado/", {"accion": "contactado"}, follow=True)
    contenido = _texto(respuesta)
    assert "Jorge Salas: contactado." in contenido
    assert f'data-aviso="pendientes">{esperados - 1}<' in contenido and "Contactados hoy" in contenido
    michi.refresh_from_db()
    assert michi.estado == EstadoRecordatorio.CONTACTADO and michi.empleado.nombre == "Sofía"
    assert f'data-aviso="recordatorios">{esperados - 1}<' in _texto(client.get("/"))


def test_TA06_registrar_una_atencion_de_estetica_con_un_hallazgo_y_avisar(client, datos):
    canela = Mascota.objects.get(nombre="Canela", cliente__telefono="8339990004")
    bano = Cita.objects.get(mascota=canela, fecha_hora_inicio__date=HOY)
    _entrar(client, "estilista")

    # 1. Agenda de estética: Canela a las 12:00 con su botón
    agenda = _texto(client.get("/estetica/"))
    assert "Mi agenda de estética" in agenda and "Canela" in agenda and "12:00" in agenda
    assert f"/estetica/citas/{bano.pk}/atender/" in agenda

    # 2. Registrar con un hallazgo y el aviso al veterinario
    registro = {
        "estado_pelaje_piel": "Pelaje opaco, nudos en las orejas",
        "hallazgos": "Costras en el lomo",
        "aviso_veterinario": "on",
        "observaciones": "Baño con shampoo hipoalergénico",
    }
    respuesta = client.post(f"/estetica/citas/{bano.pk}/atender/", registro, follow=True)
    assert "Atención de Canela registrada; la cita quedó completada. Se avisó al veterinario." in _texto(
        respuesta
    )
    bano.refresh_from_db()
    assert bano.estado == EstadoCita.COMPLETADA

    # 3. El veterinario ve el aviso en su Inicio y en el menú
    _entrar(client, "veterinario")
    inicio = _texto(client.get("/"))
    assert 'data-aviso="estetica">1<' in inicio and 'data-contador="estetica">1<' in inicio
    assert "Costras en el lomo" in inicio and "Mario Estrada Ficticio" in inicio

    # 4. El registro aparece en el historial de Canela
    historial = _texto(client.get(f"/clinica/mascotas/{canela.pk}/historial/"))
    assert "Aviso al veterinario" in historial and "Hallazgos: Costras en el lomo" in historial
    assert RegistroEstetica.objects.get(cita=bano).aviso_veterinario
