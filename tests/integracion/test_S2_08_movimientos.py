"""S2-08 y S2-09 · UI-08: ficha del producto con lotes y kardex, entradas, ajustes con confirmación (RI-04)
y alertas de inventario en su pantalla y en el Inicio del Administrador."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from inventario.models import Lote, MovimientoInventario
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

HOY = timezone.localdate()


@pytest.fixture
def admin(client, crear_usuario):
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    return client


@pytest.fixture
def vacuna():
    return fabricas.producto("VAC-001", "Vacuna múltiple canina", stock_minimo=10)


def test_S2_08_la_ficha_lista_lotes_en_orden_de_descuento_con_su_estado(admin, vacuna):
    fabricas.lote(vacuna, 20, 200, numero="TARDE")
    fabricas.lote(vacuna, 6, 15, numero="PRONTO")
    fabricas.lote(vacuna, 4, -10, numero="VIEJO")
    contenido = admin.get(f"/inventario/productos/{vacuna.pk}/").content.decode()
    assert contenido.index("VIEJO") < contenido.index("PRONTO") < contenido.index("TARDE")
    assert "Vencido" in contenido and "Por caducar" in contenido and "Vigente" in contenido
    assert "Desechar" in contenido  # el vencido con piezas se puede desechar
    assert ">26 <" in contenido  # existencias vigentes: 20 + 6; el vencido no cuenta


def test_S2_08_entrada_desde_la_ficha(admin, vacuna):
    caducidad = HOY + timedelta(days=365)
    datos = {
        "numero_lote": "abc-1",
        "fecha_caducidad": caducidad.isoformat(),
        "cantidad": "12",
        "referencia": "F-10",
    }
    respuesta = admin.post(f"/inventario/productos/{vacuna.pk}/entrada/", datos, follow=True)
    contenido = respuesta.content.decode()
    assert "Entrada registrada: 12 Dosis al lote ABC-1. Ahora tiene 12." in contenido
    assert "F-10" in contenido and "+12" in contenido  # aparece en el kardex
    assert Lote.objects.get().cantidad_disponible == Decimal("12")


def test_S2_08_no_entra_un_lote_ya_vencido(admin, vacuna):
    ayer = (HOY - timedelta(days=1)).isoformat()
    datos = {"numero_lote": "X", "fecha_caducidad": ayer, "cantidad": "5"}
    contenido = admin.post(f"/inventario/productos/{vacuna.pk}/entrada/", datos).content.decode()
    assert "Esa caducidad ya pasó" in contenido
    assert not Lote.objects.exists()


def test_S2_08_el_ajuste_muestra_el_resumen_y_solo_se_aplica_al_confirmar(admin, vacuna):
    lote = fabricas.lote(vacuna, 10, 100, numero="L-1")
    datos = {"lote": lote.pk, "sentido": "disminuir", "cantidad": "3", "motivo": "Frascos rotos"}
    resumen = admin.post(f"/inventario/productos/{vacuna.pk}/ajuste/", datos).content.decode()
    assert "¿Aplicar este ajuste?" in resumen
    assert "Pasa de <strong>10</strong> a <strong>7</strong>" in resumen
    assert not MovimientoInventario.objects.exists()  # todavía no se aplica (RI-04)

    respuesta = admin.post(
        f"/inventario/productos/{vacuna.pk}/ajuste/", {**datos, "confirmar": "1"}, follow=True
    )
    assert "Ajuste registrado en el lote L-1: ahora tiene 7." in respuesta.content.decode()
    ajuste = MovimientoInventario.objects.get()
    assert (ajuste.tipo, ajuste.cantidad, ajuste.motivo) == ("Ajuste", Decimal("-3"), "Frascos rotos")


def test_S2_08_el_ajuste_no_quita_mas_de_lo_que_hay_y_exige_motivo(admin, vacuna):
    lote = fabricas.lote(vacuna, 2, 100, numero="L-1")
    datos = {"lote": lote.pk, "sentido": "disminuir", "cantidad": "5", "motivo": "Conteo físico"}
    contenido = admin.post(f"/inventario/productos/{vacuna.pk}/ajuste/", datos).content.decode()
    assert "El lote L-1 tiene 2; no se puede quitar más." in contenido
    contenido = admin.post(
        f"/inventario/productos/{vacuna.pk}/ajuste/", {**datos, "cantidad": "1", "motivo": ""}
    )
    assert "Este campo es obligatorio." in contenido.content.decode()
    assert not MovimientoInventario.objects.exists()


def test_S2_08_desechar_un_lote_vencido_propone_quitarlo_todo(admin, vacuna):
    lote = fabricas.lote(vacuna, 4, -10, numero="VIEJO")
    respuesta = admin.get(f"/inventario/productos/{vacuna.pk}/ajuste/", {"lote": lote.pk})
    formulario = respuesta.context["formulario"]
    assert formulario.initial["sentido"] == "disminuir"
    assert formulario.initial["cantidad"] == Decimal("4")
    assert formulario.initial["motivo"] == "Lote vencido desechado"


def test_S2_09_pantalla_de_alertas(admin, vacuna):
    fabricas.lote(vacuna, 3, 12, numero="PRONTO")  # 3 < 10: stock bajo, y caduca en 12 días
    fabricas.lote(vacuna, 4, -1, numero="VIEJO")
    contenido = admin.get("/inventario/alertas/").content.decode()
    assert "Vacuna múltiple canina" in contenido
    assert "PRONTO" in contenido and "(en 12 días)" in contenido
    assert "VIEJO" in contenido and "Desechar" in contenido


def test_S2_09_el_inicio_del_administrador_cuenta_las_alertas(admin, vacuna):
    fabricas.lote(vacuna, 3, 12)
    fabricas.lote(vacuna, 4, -1)
    panel = admin.get("/").content.decode()
    assert 'data-aviso="inventario">3<' in panel  # 1 con stock bajo + 1 por caducar + 1 vencido
    assert "1 con stock bajo · 1 lote por caducar · 1 vencido" in panel
    assert 'href="/inventario/alertas/"' in panel


def test_S2_09_el_inicio_de_recepcion_no_muestra_inventario(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert 'data-aviso="inventario"' not in client.get("/").content.decode()
