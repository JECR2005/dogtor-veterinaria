"""Formularios del componente «Catálogos». Validan la captura antes de que llegue a SQL Server.

Las restricciones de la base (CHECK, NOT NULL, longitudes) siguen siendo la última defensa; aquí se
convierten en mensajes claros para la persona que captura (RI-08).
"""

import re
from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Cliente, EstatusMascota, Mascota, PreferenciaContacto, Raza, Sexo

MENSAJE_AVISO = "Sin la aceptación del aviso de privacidad no se puede registrar al cliente."

RFC = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$")  # 12 (moral) o 13 (física) caracteres
CP = re.compile(r"^\d{5}$")
REGIMEN = re.compile(r"^\d{3}$")  # clave del catálogo del SAT, por ejemplo 605 o 612


def solo_digitos(texto):
    return re.sub(r"\D", "", texto or "")


class ClienteForm(forms.ModelForm):
    """UI-05 · Alta y edición de clientes (RF-01, RNF-08)."""

    acepto_aviso_privacidad = forms.BooleanField(
        label="El cliente leyó y acepta el aviso de privacidad",
        required=True,
        error_messages={"required": MENSAJE_AVISO},
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "telefono",
            "correo",
            "direccion",
            "preferencia_contacto",
            "rfc",
            "razon_social_fiscal",
            "regimen_fiscal",
            "cp_fiscal",
            "acepto_aviso_privacidad",
        ]
        labels = {
            "nombre": "Nombre(s)",
            "apellido_paterno": "Apellido paterno",
            "apellido_materno": "Apellido materno",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
            "direccion": "Dirección",
            "preferencia_contacto": "Prefiere que lo contacten por",
            "rfc": "RFC",
            "razon_social_fiscal": "Nombre o razón social fiscal",
            "regimen_fiscal": "Régimen fiscal (clave)",
            "cp_fiscal": "Código postal fiscal",
        }
        help_texts = {
            "telefono": "10 dígitos; puede escribirlo con espacios o guiones.",
            "preferencia_contacto": "Canal para los recordatorios de vacunas y citas (RF-09).",
            "regimen_fiscal": "Clave de 3 dígitos del SAT, por ejemplo 605 o 612.",
        }
        widgets = {"preferencia_contacto": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferencia_contacto"].choices = PreferenciaContacto.choices
        if self.instance.pk:
            # El aviso se aceptó al registrar al cliente; en la edición no se vuelve a preguntar
            del self.fields["acepto_aviso_privacidad"]
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.RadioSelect):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            else:
                campo.widget.attrs["class"] = "form-control"
            if nombre == "telefono":
                campo.widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
            if nombre == "rfc":
                campo.widget.attrs["style"] = "text-transform: uppercase"

    def is_valid(self):
        valido = super().is_valid()
        for nombre in self.errors:
            if nombre in self.fields:  # Bootstrap marca en rojo el campo con error
                clase = self.fields[nombre].widget.attrs.get("class", "")
                self.fields[nombre].widget.attrs["class"] = f"{clase} is-invalid".strip()
        return valido

    def _texto(self, nombre):
        valor = (self.cleaned_data.get(nombre) or "").strip()
        return valor or None

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_apellido_paterno(self):
        return self.cleaned_data["apellido_paterno"].strip()

    def clean_apellido_materno(self):
        return self._texto("apellido_materno")

    def clean_direccion(self):
        return self._texto("direccion")

    def clean_razon_social_fiscal(self):
        return self._texto("razon_social_fiscal")

    def clean_correo(self):
        correo = self._texto("correo")
        return correo.lower() if correo else None

    def clean_telefono(self):
        telefono = solo_digitos(self.cleaned_data.get("telefono"))
        if len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe tener 10 dígitos.")
        return telefono

    def clean_rfc(self):
        rfc = (self._texto("rfc") or "").upper().replace(" ", "").replace("-", "")
        if rfc and not RFC.match(rfc):
            raise forms.ValidationError("El RFC no tiene un formato válido (12 o 13 caracteres).")
        return rfc or None

    def clean_regimen_fiscal(self):
        regimen = self._texto("regimen_fiscal")
        if regimen and not REGIMEN.match(regimen):
            raise forms.ValidationError("La clave del régimen fiscal son 3 dígitos.")
        return regimen

    def clean_cp_fiscal(self):
        cp = self._texto("cp_fiscal")
        if cp and not CP.match(cp):
            raise forms.ValidationError("El código postal son 5 dígitos.")
        return cp

    def clean(self):
        datos = super().clean()
        if datos.get("preferencia_contacto") == PreferenciaContacto.CORREO and not datos.get("correo"):
            self.add_error("correo", "Si prefiere que lo contacten por correo, capture su correo.")
        return datos


def razas_por_especie():
    """Opciones de raza agrupadas por especie («Perro», «Gato») para un <select> sin JavaScript."""
    grupos = {}
    for raza in Raza.objects.select_related("especie").order_by("especie__nombre", "nombre"):
        grupos.setdefault(raza.especie.nombre, []).append((raza.pk, raza.nombre))
    return [("", "Elija la raza")] + list(grupos.items())


class MascotaForm(forms.ModelForm):
    """UI-06 · Alta y edición de mascotas (RF-02). Al darla de alta se abre su expediente (RD-10)."""

    raza = forms.ModelChoiceField(
        Raza.objects.all(), label="Especie y raza", error_messages={"required": "Elija la raza."}
    )
    alergias = forms.CharField(
        label="Alergias conocidas",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Se mostrarán como alerta al abrir cada consulta (RF-06).",
    )
    antecedentes = forms.CharField(
        label="Antecedentes", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )

    class Meta:
        model = Mascota
        fields = [
            "nombre",
            "raza",
            "sexo",
            "fecha_nacimiento",
            "peso_actual",
            "color",
            "esterilizado",
            "estatus",
        ]
        labels = {
            "nombre": "Nombre",
            "sexo": "Sexo",
            "fecha_nacimiento": "Fecha de nacimiento",
            "peso_actual": "Peso (kg)",
            "color": "Color o señas",
            "esterilizado": "Está esterilizado(a)",
            "estatus": "Estatus",
        }
        help_texts = {"fecha_nacimiento": "Puede ser aproximada."}
        widgets = {
            "sexo": forms.RadioSelect,
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "peso_actual": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sexo"].choices = Sexo.choices
        self.fields["raza"].widget.choices = razas_por_especie()
        if self.instance.pk:
            # El expediente ya existe; alergias y antecedentes se editan en la consulta (P3)
            del self.fields["alergias"]
            del self.fields["antecedentes"]
            self.fields["estatus"].choices = EstatusMascota.choices
        else:
            del self.fields["estatus"]  # toda mascota nueva empieza Activa
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.RadioSelect | forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

    def is_valid(self):
        valido = super().is_valid()
        for nombre in self.errors:
            if nombre in self.fields:
                clase = self.fields[nombre].widget.attrs.get("class", "")
                self.fields[nombre].widget.attrs["class"] = f"{clase} is-invalid".strip()
        return valido

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_color(self):
        return (self.cleaned_data.get("color") or "").strip() or None

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get("fecha_nacimiento")
        if fecha is None:
            return None
        hoy = timezone.localdate()
        if fecha > hoy:
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura.")
        if fecha.year < hoy.year - 40:
            raise forms.ValidationError("Revise la fecha de nacimiento: indica más de 40 años.")
        return fecha

    def clean_peso_actual(self):
        peso = self.cleaned_data.get("peso_actual")
        if peso is not None and not (Decimal("0") < peso <= Decimal("150")):
            raise forms.ValidationError("El peso debe ser mayor que 0 y de hasta 150 kg.")
        return peso

    def datos_expediente(self):
        return {
            "alergias": (self.cleaned_data.get("alergias") or "").strip() or None,
            "antecedentes": (self.cleaned_data.get("antecedentes") or "").strip() or None,
        }
