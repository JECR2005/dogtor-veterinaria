"""Servicios (reglas de negocio) del componente «Inventario y compras».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1).

- RF-11, RD-03 y RD-05: existencias vigentes y distintivos por producto (S2-05); lotes y descuento
  (S2-06, S2-07).
- RF-12: proveedores (S2-04) y pedidos de compra; al recibirlos se crean los lotes (S2-10, S2-11).
- RD-07: movimientos inmodificables; correcciones mediante ajuste con motivo (S2-08).
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, DecimalField, F, Min, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from catalogos.models import Producto, Proveedor
from catalogos.services import SinAcentos

from .models import Lote, MovimientoInventario, TipoMovimiento

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


# --- S2-06 · Reglas de lote (RD-03, RD-05) -------------------------------------------
def lotes_vigentes(producto, hoy=None):
    """Lotes que se pueden usar, en el orden en que se descuentan: primero el que caduca antes (RD-05).

    Los que no caducan van al final; entre lotes con la misma caducidad, el que entró primero.
    """
    hoy = hoy or timezone.localdate()
    return (
        Lote.objects.filter(producto=producto, cantidad_disponible__gt=0)
        .filter(Q(fecha_caducidad__isnull=True) | Q(fecha_caducidad__gte=hoy))
        .order_by(F("fecha_caducidad").asc(nulls_last=True), "fecha_entrada", "id_lote")
    )


def stock_disponible(producto, hoy=None):
    """RD-05 (TU-07): suma de los lotes vigentes; los vencidos no cuentan aunque tengan piezas."""
    total = lotes_vigentes(producto, hoy).aggregate(total=Sum("cantidad_disponible"))["total"]
    return total or Decimal("0")


class ErrorInventario(Exception):
    """Operación de inventario rechazada; el mensaje dice qué ocurrió y qué hacer (RI-08)."""


class StockInsuficiente(ErrorInventario):
    pass


def _cantidad(valor):
    cantidad = Decimal(str(valor))
    if cantidad <= 0:
        raise ErrorInventario("La cantidad debe ser mayor que cero.")
    if cantidad != cantidad.quantize(Decimal("0.01")):
        raise ErrorInventario("La cantidad admite como máximo 2 decimales.")
    return cantidad


def mensaje_stock_insuficiente(producto, disponible, pedida):
    return (
        f"Stock insuficiente: hay {_texto(disponible)} {producto.unidad_medida} vigentes de "
        f"«{producto.nombre}» y se piden {_texto(pedida)}. Registre una entrada o reduzca la cantidad."
    )


def _texto(cantidad):
    cantidad = Decimal(cantidad).quantize(Decimal("0.01"))
    return f"{cantidad:,.0f}" if cantidad == cantidad.to_integral_value() else f"{cantidad:,.2f}"


# --- S2-07 · Descuento del lote que caduca primero (RD-05, TU-08, TU-09) -----------------
TIPOS_DE_SALIDA = (TipoMovimiento.VENTA, TipoMovimiento.APLICACION)


@transaction.atomic
def descontar(producto, cantidad, empleado, tipo, referencia=None, hoy=None):
    """Descuenta `cantidad` de los lotes vigentes, empezando por el que caduca primero (RD-05).

    Si no alcanza el stock disponible no descuenta nada y lanza StockInsuficiente (TU-09). Bloquea los
    lotes del producto mientras dura la transacción, para que dos ventas o aplicaciones simultáneas no
    tomen las mismas piezas (RD-09, TS-12). Lo usarán Ventas (P4) y Consulta clínica (P3).

    Devuelve la lista de (lote, cantidad descontada).
    """
    if tipo not in TIPOS_DE_SALIDA:
        raise ValueError(f"Tipo de salida no válido: {tipo}")
    cantidad = _cantidad(cantidad)
    Producto.objects.select_for_update().filter(pk=producto.pk).first()  # una salida a la vez por producto
    lotes = list(lotes_vigentes(producto, hoy).select_for_update())
    disponible = sum((lote.cantidad_disponible for lote in lotes), Decimal("0"))
    if cantidad > disponible:
        raise StockInsuficiente(mensaje_stock_insuficiente(producto, disponible, cantidad))

    descontado, pendiente = [], cantidad
    for lote in lotes:
        if pendiente <= 0:
            break
        toma = min(pendiente, lote.cantidad_disponible)
        Lote.objects.filter(pk=lote.pk).update(cantidad_disponible=F("cantidad_disponible") - toma)
        MovimientoInventario.objects.create(
            lote=lote, empleado=empleado, tipo=tipo, cantidad=-toma, referencia=referencia
        )
        lote.cantidad_disponible -= toma
        descontado.append((lote, toma))
        pendiente -= toma
    return descontado


# --- S2-08 · Entradas y ajustes con motivo (RF-11, RD-07, R08) ---------------------------
@transaction.atomic
def registrar_entrada(producto, numero_lote, cantidad, empleado, fecha_caducidad=None, referencia=None):
    """Entrada de mercancía: crea el lote, o suma al lote del mismo número y caducidad (Tabla 3.50)."""
    cantidad = _cantidad(cantidad)
    numero_lote = " ".join((numero_lote or "").split()).upper()
    if not numero_lote:
        raise ErrorInventario("Capture el número de lote.")
    existente = Lote.objects.select_for_update().filter(producto=producto, numero_lote=numero_lote).first()
    if existente and existente.fecha_caducidad != fecha_caducidad:
        raise ErrorInventario(
            f"El lote {numero_lote} ya existe con otra caducidad. Revise el número o la fecha."
        )
    if existente:
        Lote.objects.filter(pk=existente.pk).update(cantidad_disponible=F("cantidad_disponible") + cantidad)
        existente.refresh_from_db()
        lote = existente
    else:
        lote = Lote.objects.create(
            producto=producto,
            numero_lote=numero_lote,
            fecha_caducidad=fecha_caducidad,
            cantidad_disponible=cantidad,
        )
    MovimientoInventario.objects.create(
        lote=lote, empleado=empleado, tipo=TipoMovimiento.ENTRADA, cantidad=cantidad, referencia=referencia
    )
    return lote


@transaction.atomic
def ajustar(lote, cantidad_con_signo, motivo, empleado):
    """Ajuste con motivo obligatorio (R08): corrige un conteo, una merma o desecha un lote vencido.

    Es la única forma de corregir existencias: los movimientos no se editan ni se borran (RD-07).
    """
    cantidad = Decimal(str(cantidad_con_signo))
    if cantidad == 0:
        raise ErrorInventario("El ajuste no puede ser de cero.")
    _cantidad(abs(cantidad))
    motivo = " ".join((motivo or "").split())
    if len(motivo) < 5:
        raise ErrorInventario(
            "Escriba el motivo del ajuste (por ejemplo, «Conteo físico» o «Lote vencido desechado»)."
        )
    actual = Lote.objects.select_for_update().get(pk=lote.pk)
    if actual.cantidad_disponible + cantidad < 0:
        raise ErrorInventario(
            f"El ajuste dejaría el lote {actual.numero_lote} en negativo: tiene "
            f"{_texto(actual.cantidad_disponible)} y se quieren quitar {_texto(-cantidad)}."
        )
    Lote.objects.filter(pk=actual.pk).update(cantidad_disponible=F("cantidad_disponible") + cantidad)
    MovimientoInventario.objects.create(
        lote=actual, empleado=empleado, tipo=TipoMovimiento.AJUSTE, cantidad=cantidad, motivo=motivo
    )
    actual.refresh_from_db()
    return actual


# --- S2-09 · Alertas (RF-11) ---------------------------------------------------------
def alertas(hoy=None):
    """Lo que el Administrador debe atender: productos activos bajo el mínimo, lotes que caducan en
    30 días o menos y lotes vencidos que todavía tienen piezas (hay que desecharlos con un ajuste)."""
    hoy = hoy or timezone.localdate()
    activos = productos_con_existencias(hoy, Producto.objects.filter(activo=True))
    stock_bajo = activos.filter(Q(stock_vigente__lte=0) | Q(stock_vigente__lt=F("stock_minimo"))).order_by(
        "nombre"
    )
    lotes = Lote.objects.select_related("producto").filter(producto__activo=True, cantidad_disponible__gt=0)
    por_caducar = lotes.filter(
        fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=DIAS_AVISO_CADUCIDAD)
    ).order_by("fecha_caducidad", "producto__nombre")
    vencidos = lotes.filter(fecha_caducidad__lt=hoy).order_by("fecha_caducidad", "producto__nombre")
    return {"stock_bajo": list(stock_bajo), "por_caducar": list(por_caducar), "vencidos": list(vencidos)}
