"""Escenario de aceptación de P2 automatizado (TA-03, Tabla 4.14).

Recorre por las pantallas, paso a paso, el guion docs/gestion/guion_aceptacion_P2.md con los datos ficticios
de `cargar_datos_prueba`, como lo haría el Administrador con el navegador, sobre la base real de pruebas.

Sirve de regresión: si un cambio rompe el flujo del guion, la CI lo detecta antes de la evaluación.
NO sustituye la aceptación: la evalúa el personal de la clínica, sin ayuda del equipo de desarrollo, con una
calificación de al menos 4 de 5 (apartado 4.5.2.3, Tabla 3.20).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from catalogos.models import Producto
from inventario import services
from inventario.models import Lote, PedidoCompra

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]


@pytest.fixture
def administrador(client):
    """Lo que el observador prepara: datos ficticios limpios y la sesión del Administrador."""
    from seguridad.models import Usuario

    call_command("cargar_datos_prueba", mascotas=0)
    client.force_login(Usuario.objects.get(nombre_usuario="administrador"))
    return client


def _aviso_inventario(cliente):
    panel = cliente.get("/").content.decode()
    inicio = panel.index('data-aviso="inventario">') + len('data-aviso="inventario">')
    return int(panel[inicio : panel.index("<", inicio)])


def test_TA03_recibir_un_pedido_y_revisar_las_alertas(administrador):
    caducidad = timezone.localdate() + timedelta(days=365)
    vacuna = Producto.objects.get(codigo="VAC-003")
    amoxicilina = Producto.objects.get(codigo="MED-001")

    # 1. Alertas en el Inicio y en su pantalla
    assert _aviso_inventario(administrador) == 5
    alertas = administrador.get("/inventario/alertas/").content.decode()
    for texto in ("Croquetas gato adulto", "Vacuna triple felina", "VAC-001-A", "MED-001-A", "VAC-001-V"):
        assert texto in alertas, texto

    # 2. El pedido pendiente de la Distribuidora
    pedido = PedidoCompra.objects.get(estado="Pendiente", proveedor__razon_social__startswith="Distribuidora")
    ficha = administrador.get(f"/compras/pedidos/{pedido.pk}/").content.decode()
    assert pedido.folio in ficha and "$3,340.00" in ficha and "Pendiente" in ficha

    detalles = {d.producto.codigo: d for d in pedido.detalles.select_related("producto")}

    def recepcion(caducidad_vacuna):
        return {
            **_fila(detalles["VAC-003"], 20, "VTF-2701", caducidad_vacuna),
            **_fila(detalles["MED-001"], 60, "AMX-2701", caducidad),
        }

    # 3. Sin caducidad de la vacuna no se recibe nada
    contenido = administrador.post(f"/compras/pedidos/{pedido.pk}/recibir/", recepcion(None)).content.decode()
    assert "Capture la caducidad." in contenido and "no se creó ningún lote" in contenido
    assert not Lote.objects.filter(numero_lote__in=["VTF-2701", "AMX-2701"]).exists()

    # 4. Con los datos completos se recibe
    respuesta = administrador.post(
        f"/compras/pedidos/{pedido.pk}/recibir/", recepcion(caducidad), follow=True
    )
    contenido = respuesta.content.decode()
    assert f"Pedido {pedido.folio} recibido: 2 lotes con su entrada" in contenido
    assert "Lotes que entraron con este pedido" in contenido
    pedido.refresh_from_db()
    assert pedido.estado == "Recibido"

    # 5. Las existencias suben y el lote nuevo tiene su entrada
    assert services.stock_disponible(vacuna) == Decimal("23")
    assert services.stock_disponible(amoxicilina) == Decimal("120")
    ficha_vacuna = administrador.get(f"/inventario/productos/{vacuna.pk}/").content.decode()
    assert "VTF-2701" in ficha_vacuna and "+20" in ficha_vacuna and pedido.folio in ficha_vacuna

    # 6. Las alertas se recalculan
    avisos = services.alertas()
    assert [p.codigo for p in avisos["stock_bajo"]] == ["ALI-002"]
    assert _aviso_inventario(administrador) == 4

    # 7. Desechar el lote vencido de la vacuna múltiple
    vencido = Lote.objects.get(numero_lote="VAC-001-V")
    url = f"/inventario/productos/{vencido.producto_id}/ajuste/"
    propuesta = administrador.get(url, {"lote": vencido.pk}).context["formulario"].initial
    datos = {
        "lote": vencido.pk,
        "sentido": propuesta["sentido"],
        "cantidad": propuesta["cantidad"],
        "motivo": propuesta["motivo"],
    }
    resumen = administrador.post(url, datos).content.decode()
    assert "Pasa de <strong>4</strong> a <strong>0</strong>" in resumen
    administrador.post(url, {**datos, "confirmar": "1"})
    vencido.refresh_from_db()
    assert vencido.estado() == "Agotado"
    assert _aviso_inventario(administrador) == 3


def _fila(detalle, cantidad, lote, caducidad):
    prefijo = f"p{detalle.pk}"
    return {
        f"{prefijo}-cantidad_recibida": cantidad,
        f"{prefijo}-numero_lote": lote,
        f"{prefijo}-fecha_caducidad": caducidad.isoformat() if caducidad else "",
    }
