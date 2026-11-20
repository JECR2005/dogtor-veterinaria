"""Formularios del componente «Ventas y caja» (UI-17)."""

from decimal import Decimal

from django import forms

from catalogos.forms import _estilo, _marcar_errores


def _pesos(valor):
    from catalogos.templatetags.formato import pesos

    return pesos(valor)


def catalogo_de_venta():
    """Opciones para una línea: servicios y productos activos, con precio y existencias (RI-06).

    Devuelve (opciones agrupadas, {clave: artículo}, {clave: precio}). La clave es «s-<id>» o «p-<id>».
    """
    from catalogos.models import Servicio
    from catalogos.templatetags.formato import cantidad
    from inventario import services as inventario

    articulos, precios, servicios, productos = {}, {}, [], []
    for servicio in Servicio.objects.filter(activo=True).order_by("categoria", "nombre"):
        clave = f"s-{servicio.pk}"
        articulos[clave], precios[clave] = servicio, servicio.precio
        servicios.append((clave, f"{servicio.nombre} · {_pesos(servicio.precio)}"))
    for producto in inventario.productos_con_existencias().filter(activo=True).order_by("nombre"):
        clave = f"p-{producto.pk}"
        articulos[clave], precios[clave] = producto, producto.precio_venta
        existencias = (
            f"hay {cantidad(producto.stock_vigente)} {producto.unidad_medida}"
            if producto.stock_vigente > 0
            else "sin existencias"
        )
        receta = " · requiere receta" if producto.requiere_receta else ""
        productos.append(
            (
                clave,
                f"{producto.nombre} ({producto.codigo}) · {_pesos(producto.precio_venta)} · "
                f"{existencias}{receta}",
            )
        )
    opciones = [("", "—"), ("Servicios", servicios), ("Productos", productos)]
    return opciones, articulos, precios


class LineaForm(forms.Form):
    """Una línea del ticket. Las filas vacías se ignoran."""

    articulo = forms.ChoiceField(label="Producto o servicio", required=False)
    cantidad = forms.DecimalField(
        label="Cantidad",
        required=False,
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
    )
    folio_receta = forms.CharField(
        label="Folio de receta",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "R-…"}),
    )

    def __init__(self, *args, opciones=(), articulos=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.articulos = articulos or {}
        self.fields["articulo"].choices = opciones
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean(self):
        datos = super().clean()
        if not datos.get("articulo"):
            if datos.get("cantidad") or datos.get("folio_receta"):
                self.add_error("articulo", "Elija el producto o servicio.")
            return datos
        if not datos.get("cantidad"):
            self.add_error("cantidad", "Capture la cantidad.")
        return datos

    @property
    def vacia(self):
        return not getattr(self, "cleaned_data", None) or not self.cleaned_data.get("articulo")


class _LineasBase(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.opciones, self.articulos, self.precios = catalogo_de_venta()
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        return {**super().get_form_kwargs(index), "opciones": self.opciones, "articulos": self.articulos}

    def clean(self):
        if any(self.errors):
            return
        if not [f for f in self.forms if not f.vacia]:
            raise forms.ValidationError("Agregue al menos un producto o servicio al ticket.")

    def partidas(self):
        from catalogos.models import Producto

        from .services import Partida

        resultado = []
        for formulario in self.forms:
            if formulario.vacia:
                continue
            articulo = self.articulos[formulario.cleaned_data["articulo"]]
            es_producto = isinstance(articulo, Producto)
            resultado.append(
                Partida(
                    producto=articulo if es_producto else None,
                    servicio=None if es_producto else articulo,
                    cantidad=formulario.cleaned_data["cantidad"],
                    folio_receta=formulario.cleaned_data.get("folio_receta") or "",
                )
            )
        return resultado


LineasFormSet = forms.formset_factory(LineaForm, formset=_LineasBase, extra=0, min_num=6, max_num=20)


def iniciales_de(partidas):
    """Filas iniciales del formulario a partir de partidas propuestas (ticket desde una cita)."""
    return [
        {
            "articulo": f"{'p' if p.producto else 's'}-{p.articulo.pk}",
            "cantidad": p.cantidad,
            "folio_receta": p.folio_receta,
        }
        for p in partidas
    ]


class PagoForm(forms.Form):
    """S4-08 · Un abono: método, monto recibido y referencia de la tarjeta o transferencia."""

    metodo = forms.ChoiceField(label="Método de pago", widget=forms.RadioSelect)
    recibido = forms.DecimalField(
        label="Monto recibido",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="En efectivo puede ser mayor que el saldo: el sistema calcula el cambio.",
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
    )
    referencia = forms.CharField(
        label="Referencia",
        max_length=40,
        required=False,
        help_text="Autorización de la tarjeta o folio de la transferencia (opcional).",
    )

    def __init__(self, *args, **kwargs):
        from .models import MetodoPago

        super().__init__(*args, **kwargs)
        self.fields["metodo"].choices = MetodoPago.choices
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido
