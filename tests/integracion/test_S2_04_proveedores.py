"""S2-04 · UI-09 Proveedores: búsqueda, alta, edición y baja con RFC válido (RF-12). Solo el Administrador."""

import pytest

from catalogos.models import Proveedor
from inventario.forms import ProductoForm
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

VALIDO = {
    "razon_social": "Farmacéutica del Pánuco (ficticia)",
    "rfc": "fpa-200115 kx1",
    "contacto": "Marta Ríos",
    "telefono": "833 123 45 67",
    "correo": "Ventas@FPA.example.com",
    "condiciones_pago": "Crédito a 30 días",
}


@pytest.fixture
def admin(client, crear_usuario):
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    return client


def test_S2_04_alta_normaliza_rfc_telefono_y_correo(admin):
    respuesta = admin.post("/compras/proveedores/nuevo/", VALIDO, follow=True)
    proveedor = Proveedor.objects.get()
    assert (proveedor.rfc, proveedor.telefono, proveedor.correo) == (
        "FPA200115KX1",
        "8331234567",
        "ventas@fpa.example.com",
    )
    assert proveedor.activo
    assert "Proveedor «Farmacéutica del Pánuco (ficticia)» registrado." in respuesta.content.decode()


@pytest.mark.parametrize(
    "campo, valor, mensaje",
    [
        ("rfc", "ABC123", "El RFC no tiene un formato válido"),
        ("telefono", "83312", "El teléfono debe tener 10 dígitos."),
        ("razon_social", "", "Este campo es obligatorio."),
        ("correo", "no-es-correo", "Introduzca una dirección de correo electrónico válida."),
    ],
)
def test_S2_04_rechaza_datos_invalidos_y_dice_que_corregir(admin, campo, valor, mensaje):
    respuesta = admin.post("/compras/proveedores/nuevo/", {**VALIDO, campo: valor})
    assert respuesta.status_code == 200
    assert mensaje in respuesta.content.decode()
    assert not Proveedor.objects.exists()


def test_S2_04_no_repite_rfc_ni_razon_social(admin):
    fabricas.proveedor("Otra razón social", rfc="FPA200115KX1")
    fabricas.proveedor("farmacéutica del pánuco (FICTICIA)")
    contenido = admin.post("/compras/proveedores/nuevo/", VALIDO).content.decode()
    assert "Ya existe un proveedor con ese RFC." in contenido
    assert "Ya existe un proveedor con esa razón social." in contenido
    assert Proveedor.objects.count() == 2


def test_S2_04_el_rfc_es_opcional(admin):
    admin.post("/compras/proveedores/nuevo/", {**VALIDO, "rfc": ""})
    assert Proveedor.objects.get().rfc is None  # NULL: varios proveedores sin RFC (D-12)


def test_S2_04_busca_sin_acentos_por_razon_social_contacto_o_rfc(admin):
    fabricas.proveedor("Distribuidora Veterinaria del Golfo", contacto="Óscar Treviño", rfc="DVG200115KX1")
    fabricas.proveedor("Alimentos Huasteca")
    # Sin acentos, pero la ñ es otra letra en español: «trevino» no encuentra a «Treviño»
    for texto in ("veterinaria golfo", "OSCAR treviño", "dvg2001"):
        contenido = admin.get("/compras/proveedores/", {"q": texto}).content.decode()
        assert "Distribuidora Veterinaria del Golfo" in contenido and "Alimentos Huasteca" not in contenido, (
            texto
        )


def test_S2_04_baja_al_desmarcar_activo_y_se_consulta_con_el_filtro(admin):
    proveedor = fabricas.proveedor("Insumos Madero", rfc="IEM210907QR3", condiciones_pago="Contado")
    datos = {**VALIDO, "razon_social": "Insumos Madero", "rfc": "IEM210907QR3"}  # sin «activo» = desmarcado
    respuesta = admin.post(f"/compras/proveedores/{proveedor.pk}/editar/", datos, follow=True)
    assert "dado de baja; sus pedidos anteriores se conservan" in respuesta.content.decode()
    proveedor.refresh_from_db()
    assert not proveedor.activo
    assert "Insumos Madero" not in admin.get("/compras/proveedores/").content.decode()
    assert "Insumos Madero" in admin.get("/compras/proveedores/", {"inactivos": "1"}).content.decode()


def test_S2_04_el_alta_no_pregunta_si_esta_activo(admin):
    assert 'name="activo"' not in admin.get("/compras/proveedores/nuevo/").content.decode()


def test_S2_04_lista_cuenta_los_productos_activos_de_cada_proveedor(admin):
    proveedor = fabricas.proveedor("Distribuidora")
    fabricas.producto("A-1", proveedor=proveedor)
    fabricas.producto("A-2", proveedor=proveedor)
    fabricas.producto("A-3", proveedor=proveedor, activo=False)
    respuesta = admin.get("/compras/proveedores/")
    assert respuesta.context["pagina"].object_list[0].total_productos == 2


def test_S2_04_el_producto_solo_ofrece_proveedores_activos_y_conserva_el_suyo():
    activo = fabricas.proveedor("Activo")
    de_baja = fabricas.proveedor("De baja", activo=False)
    otro_de_baja = fabricas.proveedor("Otro de baja", activo=False)
    assert set(ProductoForm().fields["proveedor"].queryset) == {activo}
    producto = fabricas.producto(proveedor=de_baja)
    assert set(ProductoForm(instance=producto).fields["proveedor"].queryset) == {activo, de_baja}
    assert otro_de_baja not in ProductoForm(instance=producto).fields["proveedor"].queryset
