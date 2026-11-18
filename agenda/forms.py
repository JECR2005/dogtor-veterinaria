"""Formularios de UI-07 Agenda y cita (S1-13). Las reglas (RD-02, RD-04) viven en services.py."""

from datetime import datetime

from django import forms
from django.utils import timezone

from catalogos.models import Empleado, Servicio

PASO_MINUTOS = 15  # la agenda trabaja en bloques de 15 minutos


def _estilo(formulario):
    for campo in formulario.fields.values():
        if isinstance(campo.widget, forms.Select):
            campo.widget.attrs["class"] = "form-select"
        else:
            campo.widget.attrs["class"] = "form-control"


def _marcar_errores(formulario):
    for nombre in formulario.errors:
        if nombre in formulario.fields:
            clase = formulario.fields[nombre].widget.attrs.get("class", "")
            formulario.fields[nombre].widget.attrs["class"] = f"{clase} is-invalid".strip()


def servicios_por_categoria():
    grupos = {}
    for servicio in Servicio.objects.filter(activo=True, agendable=True).order_by("categoria", "nombre"):
        grupos.setdefault(servicio.categoria, []).append(
            (servicio.pk, f"{servicio.nombre} · {servicio.duracion_min} min")
        )
    return [("", "Elija el servicio")] + list(grupos.items())


class _FechaHoraMixin:
    def _campos_fecha_hora(self):
        self.fields["fecha"] = forms.DateField(
            label="Fecha", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
        )
        self.fields["hora"] = forms.TimeField(
            label="Hora de inicio",
            widget=forms.TimeInput(attrs={"type": "time", "step": PASO_MINUTOS * 60}, format="%H:%M"),
            help_text="En bloques de 15 minutos.",
        )

    def clean_hora(self):
        hora = self.cleaned_data["hora"]
        if hora.minute % PASO_MINUTOS or hora.second:
            raise forms.ValidationError(
                "Use horas en bloques de 15 minutos (por ejemplo 10:00, 10:15, 10:30)."
            )
        return hora

    def inicio(self):
        """Fecha y hora local elegidas, como fecha-hora con zona horaria."""
        return timezone.make_aware(datetime.combine(self.cleaned_data["fecha"], self.cleaned_data["hora"]))


class CitaForm(_FechaHoraMixin, forms.Form):
    """UI-07 · Nueva cita: servicio, empleado compatible, fecha, hora y motivo (RF-05)."""

    servicio = forms.ModelChoiceField(
        Servicio.objects.filter(activo=True, agendable=True),
        label="Servicio",
        error_messages={"required": "Elija el servicio."},
    )
    empleado = forms.ModelChoiceField(
        Empleado.objects.none(), label="Empleado", error_messages={"required": "Elija quién atiende."}
    )
    motivo = forms.CharField(
        label="Motivo o indicaciones",
        required=False,
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._campos_fecha_hora()
        self.order_fields(["servicio", "empleado", "fecha", "hora", "motivo"])
        self.fields["servicio"].widget.choices = servicios_por_categoria()
        if servicio is not None:
            from .services import empleados_para

            # RD-04 · TI-02: solo aparecen los empleados del puesto que presta el servicio
            self.fields["empleado"].queryset = empleados_para(servicio)
        self.fields["empleado"].empty_label = "Elija quién atiende"
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido


class ReprogramarForm(_FechaHoraMixin, forms.Form):
    """Reprogramar: nueva fecha, hora y, si se quiere, otro empleado del mismo puesto."""

    empleado = forms.ModelChoiceField(Empleado.objects.none(), label="Empleado")

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._campos_fecha_hora()
        self.order_fields(["empleado", "fecha", "hora"])
        from .services import empleados_para

        self.fields["empleado"].queryset = empleados_para(servicio)
        self.fields["empleado"].empty_label = None
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido


class CancelarForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo de la cancelación",
        max_length=150,
        error_messages={"required": "Escriba el motivo de la cancelación."},
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ej. El cliente pidió cambiar de día"}
        ),
    )
