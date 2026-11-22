"""Formularios del componente «Expediente clínico» (UI-11 a UI-13)."""

from decimal import Decimal

from django import forms

from catalogos.campos import DecimalSinExponente
from catalogos.forms import _estilo, _marcar_errores

from .models import Consulta, RegistroEstetica


class ConsultaForm(forms.ModelForm):
    """UI-11 · Datos de la consulta (Tabla 3.42). Síntomas y peso son obligatorios desde que se abre."""

    class Meta:
        model = Consulta
        fields = ["sintomas", "peso_kg", "temperatura_c", "diagnostico", "tratamiento", "observaciones"]
        labels = {
            "sintomas": "Síntomas y motivo de la consulta",
            "peso_kg": "Peso (kg)",
            "temperatura_c": "Temperatura (°C)",
            "diagnostico": "Diagnóstico",
            "tratamiento": "Tratamiento",
            "observaciones": "Observaciones",
        }
        help_texts = {
            "peso_kg": "Al firmar, se actualiza el peso de la mascota.",
            "diagnostico": "Obligatorio para firmar.",
        }
        field_classes = {"peso_kg": DecimalSinExponente, "temperatura_c": DecimalSinExponente}
        widgets = {
            "sintomas": forms.Textarea(attrs={"rows": 3}),
            "peso_kg": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
            "temperatura_c": forms.NumberInput(
                attrs={"step": "0.1", "min": "30", "max": "45", "inputmode": "decimal"}
            ),
            "diagnostico": forms.Textarea(attrs={"rows": 2}),
            "tratamiento": forms.Textarea(attrs={"rows": 2}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def _texto(self, nombre):
        return (self.cleaned_data.get(nombre) or "").strip() or None

    def clean_sintomas(self):
        return self.cleaned_data["sintomas"].strip()

    def clean_peso_kg(self):
        peso = self.cleaned_data["peso_kg"]
        if not Decimal("0.01") <= peso <= Decimal("150"):
            raise forms.ValidationError("Revise el peso: va de 0.01 a 150 kg.")
        return peso

    def clean_temperatura_c(self):
        temperatura = self.cleaned_data.get("temperatura_c")
        if temperatura is not None and not Decimal("30") <= temperatura <= Decimal("45"):
            raise forms.ValidationError("Revise la temperatura: va de 30 a 45 °C.")
        return temperatura

    def clean_diagnostico(self):
        return self._texto("diagnostico")

    def clean_tratamiento(self):
        return self._texto("tratamiento")

    def clean_observaciones(self):
        return self._texto("observaciones")


class CorreccionForm(ConsultaForm):
    """S5-07 · El Administrador corrige una consulta firmada; el motivo queda en la bitácora (RNF-03)."""

    motivo = forms.CharField(
        label="Motivo de la corrección",
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Obligatorio. Por ejemplo: «El veterinario reportó el peso con un dígito de más».",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["diagnostico"].required = True
        self.fields[
            "peso_kg"
        ].help_text = (
            "Si es la consulta firmada más reciente, también se corrige el peso actual de la mascota."
        )
        _estilo(self)

    def clean_motivo(self):
        motivo = " ".join(self.cleaned_data["motivo"].split())
        if len(motivo) < 10:
            raise forms.ValidationError("Explique el motivo (al menos 10 caracteres).")
        return motivo


# --- S3-07 · Aplicación (UI-12) ------------------------------------------------------
class _Simple(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido


def _etiqueta_aplicable(producto):
    from catalogos.templatetags.formato import cantidad

    lote = producto.lote_sugerido
    if lote is None:
        return f"{producto.nombre} ({producto.codigo}) · sin existencias vigentes"
    caducidad = f"caduca {lote.fecha_caducidad:%d/%m/%Y}" if lote.fecha_caducidad else "no caduca"
    return (
        f"{producto.nombre} ({producto.codigo}) · hay {cantidad(producto.stock_vigente)} "
        f"{producto.unidad_medida} · se tomará del lote {lote.numero_lote}, {caducidad}"
    )


class AplicacionForm(_Simple):
    """Producto, cantidad, dosis y próxima fecha. El lote lo elige el sistema: el que caduca antes (RD-05)."""

    producto = forms.ModelChoiceField(label="Producto", queryset=None, empty_label="Elija el producto")
    cantidad = DecimalSinExponente(
        label="Cantidad que se descuenta",
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
        initial=Decimal("1"),
        help_text="En la unidad del producto (dosis, mL, tableta…). Admite decimales.",
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
    )
    dosis = forms.CharField(label="Dosis y vía", max_length=30, help_text="Por ejemplo: 1 mL subcutánea.")
    proxima_fecha = forms.DateField(
        label="Próxima dosis",
        required=False,
        help_text="Obligatoria en vacunas y desparasitantes; genera el recordatorio (RF-09).",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def __init__(self, *args, **kwargs):
        from inventario import services as inventario

        from .services import CATEGORIAS_APLICABLES

        super().__init__(*args, **kwargs)
        productos = list(
            inventario.productos_con_existencias()
            .filter(activo=True, categoria__in=CATEGORIAS_APLICABLES)
            .order_by("categoria", "nombre")
        )
        for producto in productos:
            producto.lote_sugerido = inventario.lotes_vigentes(producto).first()
        self.fields["producto"].queryset = inventario.productos_con_existencias().filter(
            pk__in=[p.pk for p in productos]
        )
        etiquetas = {p.pk: _etiqueta_aplicable(p) for p in productos}
        self.fields["producto"].choices = [("", "Elija el producto")] + [
            (p.pk, etiquetas[p.pk]) for p in productos
        ]


# --- S3-08 · Receta (UI-13) ---------------------------------------------------------
class RecetaForm(_Simple):
    indicaciones_generales = forms.CharField(
        label="Indicaciones generales",
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Por ejemplo: dieta blanda, reposo, volver a revisión en 7 días.",
    )


class MedicamentoForm(_Simple):
    """Una partida de la receta. Las filas vacías se ignoran."""

    producto = forms.ModelChoiceField(label="Medicamento", queryset=None, required=False, empty_label="—")
    dosis = forms.CharField(label="Dosis", max_length=50, required=False)
    frecuencia = forms.CharField(label="Frecuencia", max_length=50, required=False)
    duracion_dias = forms.IntegerField(label="Días", min_value=1, max_value=365, required=False)
    indicaciones = forms.CharField(label="Indicaciones", max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        from catalogos.models import Producto

        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True).order_by("nombre")
        self.fields["producto"].label_from_instance = lambda p: f"{p.nombre} ({p.codigo})"

    def clean(self):
        datos = super().clean()
        if not datos.get("producto"):
            if any(datos.get(c) for c in ("dosis", "frecuencia", "duracion_dias", "indicaciones")):
                self.add_error("producto", "Elija el medicamento.")
            return datos
        for campo, texto in (
            ("dosis", "la dosis"),
            ("frecuencia", "la frecuencia"),
            ("duracion_dias", "los días"),
        ):
            if not datos.get(campo):
                self.add_error(campo, f"Capture {texto}.")
        return datos

    @property
    def vacia(self):
        return not getattr(self, "cleaned_data", None) or self.cleaned_data.get("producto") is None


class _MedicamentosBase(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        llenas = [f for f in self.forms if not f.vacia]
        if not llenas:
            raise forms.ValidationError("Agregue al menos un medicamento a la receta.")
        productos = [f.cleaned_data["producto"].pk for f in llenas]
        if len(productos) != len(set(productos)):
            raise forms.ValidationError("Un medicamento aparece dos veces en la receta.")

    def partidas(self):
        return [
            (
                f.cleaned_data["producto"],
                " ".join(f.cleaned_data["dosis"].split()),
                " ".join(f.cleaned_data["frecuencia"].split()),
                f.cleaned_data["duracion_dias"],
                f.cleaned_data.get("indicaciones"),
            )
            for f in self.forms
            if not f.vacia
        ]


MedicamentosFormSet = forms.formset_factory(
    MedicamentoForm, formset=_MedicamentosBase, extra=0, min_num=4, max_num=12
)


class RegistroEsteticaForm(forms.ModelForm):
    """UI-16 · Atención de estética (Tabla 3.46): pelaje y piel, hallazgos y aviso al veterinario."""

    class Meta:
        model = RegistroEstetica
        fields = ["estado_pelaje_piel", "hallazgos", "aviso_veterinario", "observaciones"]
        labels = {
            "estado_pelaje_piel": "Estado del pelaje y la piel al recibirla",
            "hallazgos": "Hallazgos",
            "aviso_veterinario": "Avisar al veterinario: el hallazgo puede ser un problema de salud",
            "observaciones": "Observaciones del servicio",
        }
        help_texts = {
            "hallazgos": "Lesiones, parásitos, bultos u otros signos. Obligatorio si avisa al veterinario.",
            "aviso_veterinario": "Aparece en el Inicio del veterinario y en el historial de la mascota.",
        }
        widgets = {
            "estado_pelaje_piel": forms.Textarea(attrs={"rows": 2}),
            "hallazgos": forms.Textarea(attrs={"rows": 2}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean(self):
        datos = super().clean()
        if datos.get("aviso_veterinario") and not (datos.get("hallazgos") or "").strip():
            self.add_error("hallazgos", "Para avisar al veterinario, describa el hallazgo.")
        return datos
