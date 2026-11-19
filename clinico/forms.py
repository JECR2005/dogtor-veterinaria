"""Formularios del componente «Expediente clínico» (UI-11 a UI-13)."""

from decimal import Decimal

from django import forms

from catalogos.forms import _estilo, _marcar_errores

from .models import Consulta


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
