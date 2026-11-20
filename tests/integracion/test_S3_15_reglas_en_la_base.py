"""S3-15 · Pruebas que intentan violar RD-01, RD-07, RD-08 y RD-09 por fuera de los servicios.

Los servicios validan antes de escribir (TU-14 a TU-16); aquí se salta el servicio, como lo haría un código
futuro con QuerySet.update(), un create() directo o SQL, y se comprueba que la base de datos siga
protegiendo la regla (cambio 2026-11-19_RD-07_RD-08_consulta_firmada.sql, apartado 4.6.1).
Cada violación va en su propia prueba: tras un error de SQL Server no se hacen más consultas.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone

from catalogos.models import CategoriaServicio, Empleado, Puesto
from clinico import services
from clinico.models import Aplicacion, Consulta, DetalleReceta, Receta, TipoAplicacion
from inventario.models import Lote, MovimientoInventario
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def escenario():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    max_ = fabricas.paciente("Max")
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    lote = fabricas.lote(vacuna, 10, 200)
    consulta = services.abrir_consulta(cita, laura, {"sintomas": "Revisión", "peso_kg": Decimal("28")})
    return laura, consulta, vacuna, lote


def _firmar(laura, consulta):
    services.guardar_consulta(
        consulta, laura, {"sintomas": "Revisión", "peso_kg": Decimal("28"), "diagnostico": "Sano"}
    )
    return services.firmar(consulta, laura)


# --- RD-07 · La consulta firmada es de solo lectura -----------------------------------------
def test_S3_15_RD07_la_base_rechaza_cambiar_el_diagnostico_de_una_firmada(escenario):
    laura, consulta, *_ = escenario
    _firmar(laura, consulta)
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Consulta.objects.filter(pk=consulta.pk).update(diagnostico="Otro diagnóstico")


def test_S3_15_RD07_la_base_rechaza_regresar_una_firmada_a_abierta(escenario):
    laura, consulta, *_ = escenario
    _firmar(laura, consulta)
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Consulta.objects.filter(pk=consulta.pk).update(estado="Abierta", fecha_firma=None)


def test_S3_15_RD07_la_base_rechaza_borrar_una_firmada(escenario):
    laura, consulta, *_ = escenario
    _firmar(laura, consulta)
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Consulta.objects.filter(pk=consulta.pk).delete()


def test_S3_15_RD07_la_base_rechaza_agregar_una_aplicacion_a_una_firmada(escenario):
    laura, consulta, _, lote = escenario
    _firmar(laura, consulta)
    with pytest.raises(IntegrityError, match="CK_aplicacion_consulta_abierta"), transaction.atomic():
        Aplicacion.objects.create(
            consulta=consulta, lote=lote, tipo=TipoAplicacion.OTRO, cantidad=Decimal("1"), dosis="1 mL"
        )


def test_S3_15_RD07_la_base_rechaza_quitar_la_aplicacion_de_una_firmada(escenario):
    laura, consulta, vacuna, _ = escenario
    (aplicacion,) = services.registrar_aplicacion(
        consulta, laura, vacuna, 1, "1 mL", HOY + timedelta(days=365)
    )
    _firmar(laura, consulta)
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Aplicacion.objects.filter(pk=aplicacion.pk).delete()


def test_S3_15_RD07_con_la_consulta_abierta_todo_sigue_funcionando(escenario):
    """Los disparadores solo detienen lo firmado: capturar, aplicar, quitar y firmar siguen igual."""
    laura, consulta, vacuna, lote = escenario
    (aplicacion,) = services.registrar_aplicacion(
        consulta, laura, vacuna, 1, "1 mL", HOY + timedelta(days=365)
    )
    services.quitar_aplicacion(aplicacion, laura)
    assert not Aplicacion.objects.exists()
    services.registrar_aplicacion(consulta, laura, vacuna, 1, "1 mL", HOY + timedelta(days=365))
    firmada = _firmar(laura, consulta)
    assert firmada.firmada and firmada.diagnostico == "Sano"
    lote.refresh_from_db()
    assert lote.cantidad_disponible == Decimal("9")


# --- RD-08 · La receta solo se emite dentro de una consulta abierta -------------------------
def test_S3_15_RD08_la_base_rechaza_una_receta_en_una_consulta_firmada(escenario):
    laura, consulta, *_ = escenario
    _firmar(laura, consulta)
    with pytest.raises(IntegrityError, match="CK_receta_consulta_abierta"), transaction.atomic():
        Receta.objects.create(consulta=consulta, folio="R-2026-99999")


def test_S3_15_RD08_la_base_rechaza_agregar_un_medicamento_despues_de_firmar(escenario):
    laura, consulta, vacuna, _ = escenario
    receta = services.emitir_receta(consulta, laura, [(vacuna, "1 mL", "Única", 1, None)])
    _firmar(laura, consulta)
    otro = fabricas.producto("MED-009", "Antibiótico", stock_minimo=0)
    with pytest.raises(IntegrityError, match="CK_detalle_receta_consulta_abierta"), transaction.atomic():
        DetalleReceta.objects.create(
            receta=receta, producto=otro, dosis="1 tableta", frecuencia="Cada 12 h", duracion_dias=5
        )


# --- RD-01 · Solo firma o receta un veterinario con cédula ----------------------------------
def test_S3_15_RD01_la_base_no_deja_quitar_la_cedula_a_un_veterinario(escenario):
    laura, *_ = escenario
    with pytest.raises(IntegrityError, match="CK_empleado_veterinario_cedula"), transaction.atomic():
        Empleado.objects.filter(pk=laura.pk).update(cedula_profesional=None)


def test_S3_15_RD01_un_empleado_que_no_es_veterinario_no_firma_aunque_tenga_cedula(escenario):
    _, consulta, *_ = escenario
    recepcion = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Rosa")
    recepcion.cedula_profesional = "87654321"  # dato erróneo capturado; el puesto manda (RD-01)
    with pytest.raises(services.ErrorClinico, match="RD-01"):
        services.firmar(consulta, recepcion)
    consulta.refresh_from_db()
    assert not consulta.firmada


# --- RD-09 · Lo aplicado se descuenta una sola vez -------------------------------------------
def test_S3_15_RD09_ni_firmar_ni_recetar_vuelven_a_descontar(escenario):
    laura, consulta, vacuna, lote = escenario
    services.registrar_aplicacion(consulta, laura, vacuna, 1, "1 mL", HOY + timedelta(days=365))
    services.emitir_receta(consulta, laura, [(vacuna, "1 mL", "Refuerzo", 1, None)])
    _firmar(laura, consulta)
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == Decimal("9")
    assert list(MovimientoInventario.objects.values_list("tipo", "cantidad")) == [
        ("Aplicación", Decimal("-1"))
    ]
