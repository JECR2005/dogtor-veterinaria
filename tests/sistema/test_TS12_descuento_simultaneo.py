"""S2-13 y S5-17 · TS-12 (Tabla 4.15): dos usuarios descuentan a la vez el último lote (RD-05, RD-09).

Criterio: ninguna existencia queda negativa. Dos hilos, cada uno con su propia conexión a SQL Server, piden la
última pieza al mismo tiempo; descontar() bloquea el producto y sus lotes, así que uno la obtiene y el otro
recibe «Stock insuficiente».

- El adelanto de P2 llama directo a descontar().
- TS-12 completo (P5) lo hace con las operaciones reales: Recepción genera un ticket con la última pieza
  mientras el Veterinario la aplica en una consulta abierta. Solo una de las dos se guarda entera; la otra no
  deja ticket, aplicación ni movimiento a medias.

Esta prueba necesita datos confirmados (transaction=True) para que los dos hilos los vean. Las tablas son
managed = False y Django no las vacía al terminar, así que la prueba borra lo que creó; para los movimientos
desactiva un momento el disparador de RD-07, solo en la base de pruebas.
"""

import threading
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection, connections
from django.utils import timezone

from agenda import services as agenda
from agenda.models import Cita
from catalogos.models import CategoriaServicio, Especie, HorarioLaboral, Puesto, Raza
from catalogos.services import abrir_expediente
from clinico import services as clinico
from clinico.models import Aplicacion, Consulta, ExpedienteClinico
from inventario import services
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from seguridad.models import BitacoraAuditoria, Usuario
from tests import fabricas
from tests.fabricas import en
from ventas import services as ventas
from ventas.models import Venta

pytestmark = [pytest.mark.sistema, pytest.mark.django_db(transaction=True)]


def _limpiar(producto, empleado):
    with connection.cursor() as cursor:
        cursor.execute("DISABLE TRIGGER dbo.TR_movimiento_inventario_inmutable ON dbo.movimiento_inventario")
        try:
            MovimientoInventario.objects.filter(lote__producto=producto).delete()
        finally:
            cursor.execute(
                "ENABLE TRIGGER dbo.TR_movimiento_inventario_inmutable ON dbo.movimiento_inventario"
            )
    Lote.objects.filter(producto=producto).delete()
    producto.delete()
    HorarioLaboral.objects.filter(empleado=empleado).delete()
    Usuario.objects.filter(empleado=empleado).delete()  # la cuenta que le da fabricas (S5-04)
    empleado.delete()


def test_TS12_dos_descuentos_simultaneos_del_ultimo_lote_no_dejan_existencias_negativas():
    assert connection.settings_dict["NAME"].startswith("test_")  # nunca sobre la base real
    empleado = fabricas.empleado(Puesto.ADMINISTRADOR, nombre="TS12")
    producto = fabricas.producto("TS12-001", "Última pieza", stock_minimo=0)
    lote = fabricas.lote(producto, 1, 100)
    salida = threading.Barrier(2, timeout=30)
    resultados = []

    def vender():
        try:
            salida.wait()
            services.descontar(producto, 1, empleado, TipoMovimiento.VENTA)
            resultados.append("vendió")
        except services.StockInsuficiente:
            resultados.append("sin stock")
        except Exception as error:  # noqa: BLE001 - cualquier otro error debe hacer fallar la prueba
            resultados.append(f"error: {error!r}")
        finally:
            connections.close_all()

    try:
        hilos = [threading.Thread(target=vender) for _ in range(2)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(timeout=60)
        assert sorted(resultados) == ["sin stock", "vendió"]
        lote.refresh_from_db()
        assert lote.cantidad_disponible == Decimal("0")
        assert list(lote.movimientos.values_list("cantidad", flat=True)) == [Decimal("-1")]
    finally:
        _limpiar(producto, empleado)


def _sin_disparador(tabla, disparador, borrar):
    with connection.cursor() as cursor:
        cursor.execute(f"DISABLE TRIGGER dbo.{disparador} ON dbo.{tabla}")
        try:
            borrar()
        finally:
            cursor.execute(f"ENABLE TRIGGER dbo.{disparador} ON dbo.{tabla}")


def _limpiar_jornada(producto, servicio, mascota, empleados, catalogos_previos):
    """Borra, en orden, lo que creó la prueba con datos confirmados (solo en la base de pruebas)."""
    cliente, raza = mascota.cliente, mascota.raza
    _sin_disparador(
        "bitacora_auditoria",
        "TR_bitacora_inmutable",
        lambda: BitacoraAuditoria.objects.filter(usuario__empleado__in=empleados).delete(),
    )
    Venta.objects.filter(cliente=cliente).delete()  # sus líneas se borran en cascada
    Aplicacion.objects.filter(consulta__expediente__mascota=mascota).delete()
    Consulta.objects.filter(expediente__mascota=mascota).delete()
    Cita.objects.filter(mascota=mascota).delete()
    ExpedienteClinico.objects.filter(mascota=mascota).delete()
    mascota.delete()
    cliente.delete()
    especies, razas = catalogos_previos
    if raza.pk not in razas:  # la raza y la especie que creó fabricas.mascota()
        especie = raza.especie
        raza.delete()
        if especie.pk not in especies:
            especie.delete()
    _sin_disparador(
        "movimiento_inventario",
        "TR_movimiento_inventario_inmutable",
        lambda: MovimientoInventario.objects.filter(lote__producto=producto).delete(),
    )
    Lote.objects.filter(producto=producto).delete()
    producto.delete()
    servicio.delete()
    for empleado in empleados:
        HorarioLaboral.objects.filter(empleado=empleado).delete()
        Usuario.objects.filter(empleado=empleado).delete()
        empleado.delete()


def test_TS12_un_ticket_y_una_aplicacion_simultaneos_de_la_ultima_pieza():
    """S5-17 · Recepción cobra la última pieza mientras el Veterinario la aplica: solo una de las dos pasa."""
    assert connection.settings_dict["NAME"].startswith("test_")  # nunca sobre la base real
    veterinario = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="TS12 Vet")
    recepcion = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="TS12 Recepción")
    consulta_general = fabricas.servicio("Consulta TS12", CategoriaServicio.CONSULTA, 30)
    catalogos_previos = (
        set(Especie.objects.values_list("pk", flat=True)),
        set(Raza.objects.values_list("pk", flat=True)),
    )
    mascota = fabricas.mascota("Pieza", "TS12")
    producto = fabricas.producto("TS12-002", "Vacuna de la última pieza", stock_minimo=0)
    lote = fabricas.lote(producto, 1, 100)
    try:
        abrir_expediente(mascota)
        cita = agenda.agendar(mascota, veterinario, consulta_general, en("10:00"))
        consulta = clinico.abrir_consulta(
            cita, veterinario, {"sintomas": "Revisión", "peso_kg": Decimal("9")}
        )
        proxima = timezone.localdate() + timedelta(days=365)
        salida = threading.Barrier(2, timeout=30)
        resultados = {}

        def intentar(quien, operacion):
            try:
                salida.wait()
                operacion()
                resultados[quien] = "guardó"
            except (ventas.ErrorVenta, clinico.ErrorClinico) as rechazo:
                resultados[quien] = str(rechazo)
            except Exception as error:  # noqa: BLE001 - cualquier otro error debe hacer fallar la prueba
                resultados[quien] = f"error: {error!r}"
            finally:
                connections.close_all()

        def cobrar():
            partida = ventas.Partida(producto=producto, cantidad=1)
            ventas.generar_ticket(mascota.cliente, recepcion, [partida])

        def aplicar():
            clinico.registrar_aplicacion(consulta, veterinario, producto, 1, "1 mL subcutánea", proxima)

        hilos = [
            threading.Thread(target=intentar, args=("ticket", cobrar)),
            threading.Thread(target=intentar, args=("aplicación", aplicar)),
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(timeout=60)

        guardaron = [quien for quien, resultado in resultados.items() if resultado == "guardó"]
        rechazos = [resultado for resultado in resultados.values() if resultado != "guardó"]
        assert len(guardaron) == 1, resultados
        assert len(rechazos) == 1 and rechazos[0].startswith("Stock insuficiente"), resultados

        # Ninguna existencia negativa y nada a medias: un solo movimiento, y solo el ticket o la aplicación
        lote.refresh_from_db()
        assert lote.cantidad_disponible == Decimal("0")
        movimientos = list(lote.movimientos.values_list("tipo", "cantidad"))
        hay_ticket = Venta.objects.filter(cliente=mascota.cliente).exists()
        hay_aplicacion = Aplicacion.objects.filter(consulta=consulta).exists()
        if guardaron == ["ticket"]:
            assert movimientos == [(TipoMovimiento.VENTA, Decimal("-1"))]
            assert hay_ticket and not hay_aplicacion
        else:
            assert movimientos == [(TipoMovimiento.APLICACION, Decimal("-1"))]
            assert hay_aplicacion and not hay_ticket
    finally:
        _limpiar_jornada(producto, consulta_general, mascota, [veterinario, recepcion], catalogos_previos)
