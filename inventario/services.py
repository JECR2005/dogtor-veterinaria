"""Servicios (reglas de negocio) del componente «Inventario y compras».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

- RF-11, RD-03 y RD-05: existencias vigentes y distintivos por producto (S2-05); lotes y descuento
  (S2-06, S2-07).
- RF-12: proveedores (S2-04) y pedidos de compra; al recibirlos se crean los lotes (S2-10, S2-11).
- RD-07: movimientos inmodificables; correcciones mediante ajuste con motivo (S2-08).
"""

from datetime import timedelta

from django.db.models import Count, DecimalField, F, Min, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from catalogos.models import Producto, Proveedor
from catalogos.services import SinAcentos

DIAS_AVISO_CADUCIDAD = 30  # RF-11: la alerta aparece 30 días antes de caducar

CERO = Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))


def productos_con_existencias(hoy=None, productos=None):
    """Productos con sus existencias calculadas a partir de los lotes (el stock no se guarda, apartado 3.4).

    - `stock_vigente`: suma de los lotes que no han caducado; un lote que caduca hoy todavía vale (RD-03).
    - `proxima_caducidad`: la fecha más cercana de un lote vigente con existencias.
    - `cantidad_vencida`: lo que queda en lotes ya vencidos, que no se puede vender ni aplicar.

    Es el mismo cálculo que la vista `vista_stock_disponible` de `bd/02_vistas.sql`.
    """
    hoy = hoy or timezone.localdate()
    vigente = Q(lotes__fecha_caducidad__isnull=True) | Q(lotes__fecha_caducidad__gte=hoy)
    productos = Producto.objects.all() if productos is None else productos
    return productos.select_related("proveedor").annotate(
        stock_vigente=Coalesce(Sum("lotes__cantidad_disponible", filter=vigente), CERO),
        proxima_caducidad=Min(
            "lotes__fecha_caducidad",
            filter=Q(lotes__cantidad_disponible__gt=0, lotes__fecha_caducidad__gte=hoy),
        ),
        cantidad_vencida=Coalesce(
            Sum(
                "lotes__cantidad_disponible",
                filter=Q(lotes__fecha_caducidad__lt=hoy, lotes__cantidad_disponible__gt=0),
            ),
            CERO,
        ),
    )


def distintivos(producto, hoy=None):
    """Distintivos de RI-02 para un producto anotado con `productos_con_existencias`.

    Devuelve una lista de (clave, texto) en el orden en que se muestran.
    """
    hoy = hoy or timezone.localdate()
    resultado = []
    if producto.stock_vigente <= 0:
        resultado.append(("sin_existencias", "Sin existencias"))
    elif producto.stock_vigente < producto.stock_minimo:
        resultado.append(("stock_bajo", "Stock bajo"))
    limite = hoy + timedelta(days=DIAS_AVISO_CADUCIDAD)
    if producto.proxima_caducidad and producto.proxima_caducidad <= limite:
        dias = (producto.proxima_caducidad - hoy).days
        texto = "Caduca hoy" if dias == 0 else f"Caduca en {dias} día{'s' if dias != 1 else ''}"
        resultado.append(("por_caducar", texto))
    if producto.cantidad_vencida > 0:
        resultado.append(("vencido", "Lote vencido"))
    return resultado


FILTROS_ALERTA = {
    "stock_bajo": "Stock bajo o sin existencias",
    "por_caducar": f"Caduca en {DIAS_AVISO_CADUCIDAD} días o menos",
    "vencido": "Con lotes vencidos",
}


def buscar_productos(texto="", categoria="", alerta="", incluir_inactivos=False, hoy=None):
    """UI-08 · Productos por código o nombre (sin importar acentos), categoría y tipo de alerta."""
    hoy = hoy or timezone.localdate()
    base = Producto.objects.all()
    if not incluir_inactivos:
        base = base.filter(activo=True)
    if categoria:
        base = base.filter(categoria=categoria)
    palabras = (texto or "").split()
    if palabras:
        # «vacuna multiple» encuentra «Vacuna múltiple canina» (RI-13); primero se filtra y luego se suma
        coincidencias = base.annotate(_nombre=SinAcentos("nombre"))
        for palabra in palabras:
            coincidencias = coincidencias.filter(Q(codigo__icontains=palabra) | Q(_nombre__icontains=palabra))
        base = Producto.objects.filter(pk__in=coincidencias.values("pk"))
    productos = productos_con_existencias(hoy, base)
    if alerta == "stock_bajo":
        productos = productos.filter(Q(stock_vigente__lte=0) | Q(stock_vigente__lt=F("stock_minimo")))
    elif alerta == "por_caducar":
        productos = productos.filter(proxima_caducidad__lte=hoy + timedelta(days=DIAS_AVISO_CADUCIDAD))
    elif alerta == "vencido":
        productos = productos.filter(cantidad_vencida__gt=0)
    return productos.order_by("nombre", "pk")


def buscar_proveedores(texto="", incluir_inactivos=False):
    """UI-09 · Proveedores por razón social, RFC o contacto, con cuántos productos activos surten."""
    base = Proveedor.objects.all()
    if not incluir_inactivos:
        base = base.filter(activo=True)
    palabras = (texto or "").split()
    if palabras:
        coincidencias = base.annotate(_razon=SinAcentos("razon_social"), _contacto=SinAcentos("contacto"))
        for palabra in palabras:
            coincidencias = coincidencias.filter(
                Q(_razon__icontains=palabra) | Q(_contacto__icontains=palabra) | Q(rfc__icontains=palabra)
            )
        base = Proveedor.objects.filter(pk__in=coincidencias.values("pk"))
    return base.annotate(total_productos=Count("productos", filter=Q(productos__activo=True))).order_by(
        "razon_social", "pk"
    )
