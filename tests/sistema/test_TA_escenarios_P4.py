"""Escenarios de aceptación de P4 automatizados (TA-07 y TA-08, Tabla 4.14).

Recorren por las pantallas, paso a paso, el guion docs/gestion/guion_aceptacion_P4.md con los datos ficticios
de `cargar_datos_prueba` (tickets de Jorge Salas y Pedro Ibarra, y Toby por cobrar), como lo harían la
Recepcionista y el Administrador con el navegador, sobre la base real de pruebas.

Sirven de regresión: si un cambio rompe el flujo del guion, la CI lo detecta antes de la evaluación.
NO sustituyen la aceptación: la evalúa el personal de la clínica, sin ayuda del equipo de desarrollo, con una
calificación de al menos 4 de 5 (apartado 4.5.2.3, Tabla 3.20).
"""

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from agenda.models import Cita
from catalogos.models import Producto, Servicio
from inventario import services as inventario
from inventario.models import MovimientoInventario
from seguridad.models import Usuario
from ventas.models import Venta

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

HOY = timezone.localdate()
FOLIO = f"T-{HOY:%Y}-"


@pytest.fixture
def datos():
    call_command("cargar_datos_prueba", mascotas=0)


def _entrar(client, cuenta):
    client.force_login(Usuario.objects.get(nombre_usuario=cuenta))


def _texto(respuesta):
    return respuesta.content.decode()


def _neto(pantalla, metodo):
    inicio = pantalla.index(f'data-metodo="{metodo}"')
    celda = pantalla.index("data-neto>", inicio) + len("data-neto>")
    return pantalla[celda : pantalla.index("<", celda)]


def test_TA07_corte_de_caja_de_un_dia_con_pagos_parciales(client, datos):
    _entrar(client, "recepcion")

    # 1. El Inicio avisa del ticket con saldo de Pedro
    inicio = _texto(client.get("/"))
    assert 'data-aviso="tickets_con_saldo">1<' in inicio and "Por cobrar: $260.00" in inicio

    # 2. Cobrar a Toby desde «Por cobrar hoy»: consulta y desparasitante aplicado (D-20)
    cita = Cita.objects.get(mascota__nombre="Toby", mascota__cliente__telefono="8339990005")
    lista = _texto(client.get("/ventas/"))
    assert "Por cobrar hoy" in lista and f"/ventas/nuevo/?cita={cita.pk}" in lista
    propuesta = _texto(client.get(f"/ventas/nuevo/?cita={cita.pk}"))
    assert "Consulta general · $400.00" in propuesta and "Aplicación de desparasitante · $350.00" in propuesta
    cobro = Servicio.objects.get(nombre="Aplicación de desparasitante")
    lineas = {
        "lineas-TOTAL_FORMS": "6",
        "lineas-INITIAL_FORMS": "2",
        "lineas-MIN_NUM_FORMS": "6",
        "lineas-MAX_NUM_FORMS": "20",
        "lineas-0-articulo": f"s-{cita.servicio_id}",
        "lineas-0-cantidad": "1",
        "lineas-1-articulo": f"s-{cobro.pk}",
        "lineas-1-cantidad": "1",
    }
    respuesta = client.post(f"/ventas/nuevo/?cita={cita.pk}", lineas, follow=True)
    assert f"Ticket {FOLIO}00003 generado por $750.00. Registre el pago." in _texto(respuesta)
    toby = Venta.objects.get(folio_ticket=f"{FOLIO}00003")
    url = f"/ventas/tickets/{toby.pk}/"

    # 3. Requiere factura con los datos fiscales de Marta Ríos
    contenido = _texto(client.post(f"{url}factura/", {"requiere": "si"}, follow=True))
    assert (
        "requiere factura con los datos fiscales de Marta Ríos" in contenido and "RIFM850312AB4" in contenido
    )

    # 4. y 5. Pago parcial con transferencia y el resto en efectivo con cambio
    datos_pago = {"metodo": "Transferencia", "recibido": "400", "referencia": "SPEI 123456"}
    contenido = _texto(client.post(f"{url}pagar/", datos_pago, follow=True))
    assert "Pago de $400.00 en transferencia registrado. Saldo: $350.00." in contenido
    contenido = _texto(client.post(f"{url}pagar/", {"metodo": "Efectivo", "recibido": "500"}, follow=True))
    assert "Pago de $350.00 en efectivo registrado. Entregue $150.00 de cambio. Ticket pagado." in contenido

    # 6. Abono de Pedro en efectivo exacto
    pedro = Venta.objects.get(folio_ticket=f"{FOLIO}00002")
    contenido = _texto(
        client.post(
            f"/ventas/tickets/{pedro.pk}/pagar/", {"metodo": "Efectivo", "recibido": "100"}, follow=True
        )
    )
    assert "Pago de $100.00 en efectivo registrado. Saldo: $160.00." in contenido

    # 7. El corte coincide con los pagos del día
    corte = _texto(client.get("/ventas/corte/"))
    assert (_neto(corte, "Efectivo"), _neto(corte, "Tarjeta"), _neto(corte, "Transferencia")) == (
        "$920.00",
        "$300.00",
        "$400.00",
    )
    assert "Recibido $1,100.00 · cambio entregado $180.00" in corte
    assert "data-total-neto>$1,620.00<" in corte

    # 8. PDF del corte y 9. el Inicio ya solo debe $160.00
    assert client.get("/ventas/corte/pdf/")["Content-Type"] == "application/pdf"
    assert "Por cobrar: $160.00" in _texto(client.get("/"))

    # 10. El Administrador ve el mismo corte
    _entrar(client, "administrador")
    assert "data-total-neto>$1,620.00<" in _texto(client.get("/ventas/corte/"))


def test_TA08_cancelar_un_ticket_pagado_con_cada_rol(client, datos):
    jorge = Venta.objects.get(folio_ticket=f"{FOLIO}00001")
    url = f"/ventas/tickets/{jorge.pk}/"
    croquetas = Producto.objects.get(codigo="ALI-001")
    collar = Producto.objects.get(codigo="ACC-001")

    # 1. y 2. La Recepcionista no puede: sin botón y «Acceso denegado» por dirección directa
    _entrar(client, "recepcion")
    pantalla = _texto(client.get(url))
    assert "Pagada" in pantalla and "solo el Administrador lo puede cancelar" in pantalla
    respuesta = client.get(f"{url}cancelar/")
    assert respuesta.status_code == 403 and "Acceso denegado" in _texto(respuesta)

    # 3. Existencias antes de cancelar
    assert (inventario.stock_disponible(croquetas), inventario.stock_disponible(collar)) == (30, 11)

    # 4. El Administrador sí: resumen, motivo y confirmación
    _entrar(client, "administrador")
    resumen = _texto(client.get(f"{url}cancelar/"))
    assert "devolución de $470.00 en efectivo" in resumen
    assert "Regresan <strong>1 Bolsa</strong> de Croquetas perro adulto 2 kg al lote ALI-001-A" in resumen
    assert "Regresan <strong>1 Pieza</strong> de Collar ajustable mediano al lote ACC-001-A" in resumen
    contenido = _texto(client.post(f"{url}cancelar/", {"motivo": "Producto defectuoso"}, follow=True))
    assert f"Ticket {FOLIO}00001 cancelado. Quedó registrado en la bitácora." in contenido
    assert "Ticket cancelado</strong> por Andrés Duarte Ficticio: Producto defectuoso" in contenido
    jorge.refresh_from_db()
    devolucion = jorge.pagos.get(tipo="Devolución")
    assert (devolucion.metodo, devolucion.monto) == ("Efectivo", Decimal("470.00"))

    # 5. El inventario se restauró con movimientos «Devolución»
    assert (inventario.stock_disponible(croquetas), inventario.stock_disponible(collar)) == (31, 12)
    referencias = MovimientoInventario.objects.filter(tipo="Devolución").values_list("referencia", flat=True)
    assert set(referencias) == {f"Cancelación {FOLIO}00001"}

    # 6. El corte muestra la devolución en efectivo
    corte = _texto(client.get("/ventas/corte/"))
    assert _neto(corte, "Efectivo") == "$0.00" and "data-total-neto>$300.00<" in corte
