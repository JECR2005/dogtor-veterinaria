"""Formularios del componente «Inventario y compras» (UI-08 y UI-09).

Validan la captura antes de que llegue a SQL Server; las restricciones de la base (UNIQUE, CHECK) siguen
siendo la última defensa. Los mensajes dicen qué corregir (RI-08).
"""

from decimal import Decimal

from django import forms
from django.utils import timezone

from catalogos.forms import RFC, _estilo, _marcar_errores, solo_digitos
from catalogos.models import CategoriaProducto, Producto, Proveedor
from catalogos.templatetags.formato import cantidad as formato_cantidad

from .models import Lote

PRECIO_MAXIMO = Decimal("99999.99")


class _Formulario(forms.ModelForm):
    """Estilo de Bootstrap, campos en rojo cuando tienen error y textos opcionales guardados como NULL."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and "activo" in self.fields:
            del self.fields["activo"]  # todo registro nuevo nace activo
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def _texto(self, nombre):
        valor = " ".join((self.cleaned_data.get(nombre) or "").split())
        return valor or None


class ProveedorForm(_Formulario):
    """UI-09 · Proveedor con sus condiciones de pago (RF-12)."""

    # Más largo que la columna (13) para aceptar «FPA-200115-KX1»; clean_rfc quita guiones y espacios
    rfc = forms.CharField(
        label="RFC",
        required=False,
        max_length=20,
        help_text="Opcional. 12 caracteres si es persona moral o 13 si es persona física.",
    )

    class Meta:
        model = Proveedor
        fields = ["razon_social", "rfc", "contacto", "telefono", "correo", "condiciones_pago", "activo"]
        labels = {
            "razon_social": "Razón social",
            "contacto": "Persona de contacto",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
            "condiciones_pago": "Condiciones de pago",
            "activo": "Proveedor activo",
        }
        help_texts = {
            "telefono": "10 dígitos; puede escribirlo con espacios o guiones.",
            "condiciones_pago": "Por ejemplo: Contado, Crédito a 30 días.",
            "activo": "Un proveedor inactivo ya no aparece al registrar productos ni pedidos, "
            "pero se conserva en los pedidos anteriores.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rfc"].widget.attrs["style"] = "text-transform: uppercase"
        self.fields["telefono"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})

    def clean_razon_social(self):
        razon_social = self._texto("razon_social")
        repetidos = Proveedor.objects.filter(razon_social__iexact=razon_social).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError("Ya existe un proveedor con esa razón social.")
        return razon_social

    def clean_rfc(self):
        rfc = (self.cleaned_data.get("rfc") or "").upper().replace(" ", "").replace("-", "")
        if not rfc:
            return None
        if not RFC.match(rfc):
            raise forms.ValidationError("El RFC no tiene un formato válido (12 o 13 caracteres).")
        if Proveedor.objects.filter(rfc=rfc).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un proveedor con ese RFC.")
        return rfc

    def clean_contacto(self):
        return self._texto("contacto")

    def clean_telefono(self):
        telefono = solo_digitos(self.cleaned_data.get("telefono"))
        if len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe tener 10 dígitos.")
        return telefono

    def clean_correo(self):
        correo = self._texto("correo")
        return correo.lower() if correo else None

    def clean_condiciones_pago(self):
        return self._texto("condiciones_pago")


class ProductoForm(_Formulario):
    """UI-08 · Producto del catálogo (RF-11). Sus existencias se llevan por lote, no aquí (RD-05)."""

    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "categoria",
            "unidad_medida",
            "precio_venta",
            "stock_minimo",
            "proveedor",
            "requiere_receta",
            "activo",
        ]
        labels = {
            "codigo": "Código",
            "nombre": "Nombre comercial",
            "categoria": "Categoría",
            "unidad_medida": "Unidad de medida",
            "precio_venta": "Precio de venta (MXN)",
            "stock_minimo": "Stock mínimo",
            "proveedor": "Proveedor habitual",
            "requiere_receta": "Requiere receta para venderse",
            "activo": "Producto activo",
        }
        help_texts = {
            "codigo": "Código interno o de barras. No se repite.",
            "unidad_medida": "Cómo se cuenta: Pieza, Dosis, Tableta, mL, kg… "
            "Las existencias admiten decimales.",
            "precio_venta": "Precio vigente. Los tickets guardan el precio del momento en que se generan "
            "(RD-11).",
            "stock_minimo": "Cuando las existencias vigentes bajan de este número aparece la alerta "
            "de reabasto.",
            "requiere_receta": "Al cobrarlo se pedirá el folio de una receta válida (RD-12).",
            "activo": "Un producto inactivo ya no se ofrece, pero se conserva en tickets y movimientos "
            "anteriores.",
        }
        widgets = {
            "precio_venta": forms.NumberInput(attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}),
            "stock_minimo": forms.NumberInput(attrs={"step": "1", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].choices = [("", "Elija la categoría")] + list(CategoriaProducto.choices)
        # Solo proveedores activos, más el que ya tenía el producto aunque se haya dado de baja
        proveedores = Proveedor.objects.filter(activo=True)
        if self.instance.proveedor_id:
            proveedores = proveedores | Proveedor.objects.filter(pk=self.instance.proveedor_id)
        self.fields["proveedor"].queryset = proveedores.order_by("razon_social")
        self.fields["proveedor"].empty_label = "Sin proveedor habitual"
        self.fields["codigo"].widget.attrs["style"] = "text-transform: uppercase"
        self.fields["unidad_medida"].widget.attrs["list"] = "unidades"

    def clean_codigo(self):
        codigo = "".join((self.cleaned_data.get("codigo") or "").split()).upper()
        if Producto.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto con ese código.")
        return codigo

    def clean_nombre(self):
        return self._texto("nombre")

    def clean_unidad_medida(self):
        return self._texto("unidad_medida")

    def clean_precio_venta(self):
        precio = self.cleaned_data["precio_venta"]
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        if precio > PRECIO_MAXIMO:
            raise forms.ValidationError("Revise el precio: es mayor a $99,999.99.")
        return precio

    def clean_stock_minimo(self):
        minimo = self.cleaned_data["stock_minimo"]
        if minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return minimo


# --- S2-08 · Movimientos de inventario (UI-08) ---------------------------------------
class _FormularioSimple(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido


class EntradaForm(_FormularioSimple):
    """Entrada de mercancía a un lote (Tabla 3.50, tipo Entrada).

    Los pedidos recibidos la generan solos (S2-11); esta es para la mercancía que llega sin pedido.
    """

    numero_lote = forms.CharField(label="Número de lote", max_length=30)
    fecha_caducidad = forms.DateField(
        label="Caducidad",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        help_text="Déjela vacía solo si el producto no caduca (por ejemplo, un collar).",
    )
    cantidad = forms.DecimalField(
        label="Cantidad",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
    )
    referencia = forms.CharField(
        label="Referencia",
        max_length=40,
        required=False,
        help_text="Opcional: folio de factura o remisión.",
    )

    def __init__(self, *args, hoy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hoy = hoy

    def clean_fecha_caducidad(self):
        caducidad = self.cleaned_data.get("fecha_caducidad")
        if caducidad and caducidad < (self.hoy or timezone.localdate()):
            raise forms.ValidationError(
                "Esa caducidad ya pasó: un lote vencido no puede entrar al inventario (RD-03)."
            )
        return caducidad

    def clean_referencia(self):
        return " ".join((self.cleaned_data.get("referencia") or "").split()) or None


def _etiqueta_lote(lote):
    caducidad = f"{lote.fecha_caducidad:%d/%m/%Y}" if lote.fecha_caducidad else "sin caducidad"
    return f"{lote.numero_lote} · {caducidad} · hay {formato_cantidad(lote.cantidad_disponible)}"


SENTIDOS = [
    ("aumentar", "Aumentar (llegó o se encontró de más)"),
    ("disminuir", "Disminuir (merma, daño o desecho)"),
]


class AjusteForm(_FormularioSimple):
    """Ajuste con motivo obligatorio (R08). Se confirma antes de aplicarse (RI-04)."""

    lote = forms.ModelChoiceField(label="Lote", queryset=None, empty_label="Elija el lote")
    sentido = forms.ChoiceField(label="El ajuste", choices=SENTIDOS, widget=forms.RadioSelect)
    cantidad = forms.DecimalField(
        label="Cantidad",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
    )
    motivo = forms.CharField(
        label="Motivo",
        max_length=150,
        min_length=5,
        help_text="Queda registrado y no se puede borrar (RD-07). Ej.: Conteo físico, Frasco roto, "
        "Lote vencido desechado.",
    )

    def __init__(self, producto, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lote"].queryset = Lote.objects.filter(producto=producto).order_by(
            "fecha_caducidad", "id_lote"
        )
        self.fields["lote"].label_from_instance = _etiqueta_lote

    def clean_motivo(self):
        return " ".join(self.cleaned_data["motivo"].split())

    def cantidad_con_signo(self):
        cantidad = self.cleaned_data["cantidad"]
        return cantidad if self.cleaned_data["sentido"] == "aumentar" else -cantidad
