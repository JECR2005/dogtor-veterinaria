"""Formularios del componente «Catálogos». Validan la captura antes de que llegue a SQL Server.

Las restricciones de la base (CHECK, NOT NULL, longitudes) siguen siendo la última defensa; aquí se
convierten en mensajes claros para la persona que captura (RI-08).
"""

import re
from datetime import time
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from seguridad.models import Rol, Usuario

from .models import (
    CategoriaServicio,
    Cliente,
    DiaSemana,
    Empleado,
    EstatusMascota,
    Mascota,
    PreferenciaContacto,
    Puesto,
    Raza,
    Servicio,
    Sexo,
)

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


# --- UI-03 · Empleados y usuarios (S1-10) -------------------------------------
CEDULA = re.compile(r"^\d{7,8}$")
NOMBRE_USUARIO = re.compile(r"^[a-z0-9._-]{3,30}$")


def _estilo(formulario):
    for campo in formulario.fields.values():
        if isinstance(campo.widget, forms.RadioSelect | forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        elif isinstance(campo.widget, forms.Select):
            campo.widget.attrs["class"] = "form-select"
        else:
            campo.widget.attrs["class"] = "form-control"


def _marcar_errores(formulario):
    for nombre in formulario.errors:
        if nombre in formulario.fields:
            clase = formulario.fields[nombre].widget.attrs.get("class", "")
            formulario.fields[nombre].widget.attrs["class"] = f"{clase} is-invalid".strip()


class EmpleadoForm(forms.ModelForm):
    """UI-03 · Datos del empleado (RF-03). La cédula es obligatoria para Veterinario (RD-01, TU-05)."""

    class Meta:
        model = Empleado
        fields = [
            "nombre",
            "apellidos",
            "puesto",
            "cedula_profesional",
            "telefono",
            "fecha_ingreso",
            "activo",
        ]
        labels = {
            "nombre": "Nombre(s)",
            "apellidos": "Apellidos",
            "puesto": "Puesto",
            "cedula_profesional": "Cédula profesional",
            "telefono": "Teléfono",
            "fecha_ingreso": "Fecha de ingreso",
            "activo": "Empleado activo",
        }
        help_texts = {"cedula_profesional": "Obligatoria para Veterinario: 7 u 8 dígitos."}
        widgets = {"fecha_ingreso": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["puesto"].choices = [("", "Elija el puesto")] + list(Puesto.choices)
        if not self.instance.pk:
            del self.fields["activo"]
            self.fields["fecha_ingreso"].initial = timezone.localdate()
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_apellidos(self):
        return self.cleaned_data["apellidos"].strip()

    def clean_cedula_profesional(self):
        cedula = solo_digitos(self.cleaned_data.get("cedula_profesional")) or None
        if cedula and not CEDULA.match(cedula):
            raise forms.ValidationError("La cédula profesional tiene 7 u 8 dígitos.")
        return cedula

    def clean_telefono(self):
        telefono = solo_digitos(self.cleaned_data.get("telefono")) or None
        if telefono and len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe tener 10 dígitos.")
        return telefono


class HorarioSemanalForm(forms.Form):
    """Horario laboral de lunes a sábado (Tabla 3.37). Día sin horas = no trabaja ese día.

    Debe quedar dentro del horario de atención de la clínica (9:00 a 19:00, RNF-06). La agenda (RD-02)
    solo acepta citas dentro de este horario.
    """

    def __init__(self, *args, puesto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.puesto = puesto
        for dia, nombre in DiaSemana.choices:
            for parte in ("entrada", "salida"):
                self.fields[f"{parte}_{dia}"] = forms.TimeField(
                    label=f"{nombre}: {parte}",
                    required=False,
                    widget=forms.TimeInput(attrs={"type": "time", "step": 900}, format="%H:%M"),
                )
        _estilo(self)

    def dias(self):
        """[(número, nombre, campo entrada, campo salida)] para la plantilla."""
        return [
            (dia, nombre, self[f"entrada_{dia}"], self[f"salida_{dia}"]) for dia, nombre in DiaSemana.choices
        ]

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean(self):
        datos = super().clean()
        atencion = settings.DOGTOR_HORARIO_ATENCION
        apertura = time.fromisoformat(atencion["apertura"])
        cierre = time.fromisoformat(atencion["cierre"])
        jornadas = []
        for dia, nombre in DiaSemana.choices:
            entrada, salida = datos.get(f"entrada_{dia}"), datos.get(f"salida_{dia}")
            if f"entrada_{dia}" in self.errors or f"salida_{dia}" in self.errors:
                continue
            if entrada is None and salida is None:
                continue
            if entrada is None or salida is None:
                self.add_error(
                    f"salida_{dia}" if salida is None else f"entrada_{dia}",
                    f"{nombre}: capture la hora de entrada y la de salida, o deje ambas vacías.",
                )
            elif salida <= entrada:
                self.add_error(f"salida_{dia}", f"{nombre}: la salida debe ser después de la entrada.")
            elif entrada < apertura or salida > cierre:
                self.add_error(
                    f"entrada_{dia}",
                    f"{nombre}: el horario debe estar entre {apertura:%H:%M} y {cierre:%H:%M} "
                    "(horario de atención).",
                )
            else:
                jornadas.append((dia, entrada, salida))
        if not self.errors and not jornadas and self.puesto in (Puesto.VETERINARIO, Puesto.ESTILISTA):
            raise forms.ValidationError(
                "El veterinario y el estilista necesitan al menos un día de horario para recibir citas."
            )
        self.jornadas = jornadas
        return datos


class CuentaForm(forms.Form):
    """Cuenta de acceso del empleado (Tabla 3.38). RF-03: no se crea una cuenta sin rol."""

    crear = forms.BooleanField(label="Crear cuenta de acceso al sistema", required=False)
    nombre_usuario = forms.CharField(
        label="Usuario",
        max_length=30,
        required=False,
        help_text="De 3 a 30 caracteres: minúsculas, números, punto, guion o guion bajo.",
    )
    rol = forms.ChoiceField(label="Rol", choices=[("", "Elija el rol")] + list(Rol.choices), required=False)
    activa = forms.BooleanField(label="Cuenta activa", required=False)
    contrasena = forms.CharField(
        label="Contraseña", required=False, widget=forms.PasswordInput(render_value=False)
    )
    confirmacion = forms.CharField(label="Confirme la contraseña", required=False, widget=forms.PasswordInput)

    def __init__(self, *args, cuenta=None, administrador=None, **kwargs):
        self.cuenta = cuenta
        self.administrador = administrador
        if cuenta is not None:
            kwargs.setdefault(
                "initial",
                {"nombre_usuario": cuenta.nombre_usuario, "rol": cuenta.rol, "activa": cuenta.activo},
            )
        super().__init__(*args, **kwargs)
        if cuenta is None:
            del self.fields["activa"]
        else:
            del self.fields["crear"]
            self.fields["nombre_usuario"].disabled = True
            self.fields["contrasena"].label = "Nueva contraseña"
            self.fields["contrasena"].help_text = "Déjela vacía para conservar la actual."
            if self.es_propia:
                # El Administrador no puede quitarse su propio acceso ni su rol
                self.fields["rol"].disabled = True
                self.fields["activa"].disabled = True
        self.fields["nombre_usuario"].widget.attrs["autocomplete"] = "off"
        self.fields["contrasena"].widget.attrs["autocomplete"] = "new-password"
        self.fields["confirmacion"].widget.attrs["autocomplete"] = "new-password"
        _estilo(self)

    @property
    def es_propia(self):
        return (
            self.cuenta is not None
            and self.administrador is not None
            and self.cuenta.pk == self.administrador.pk
        )

    @property
    def aplica(self):
        """True si hay una cuenta que crear o actualizar."""
        return self.cuenta is not None or bool(self.cleaned_data.get("crear"))

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean_nombre_usuario(self):
        if self.cuenta is not None:
            return self.cuenta.nombre_usuario
        return (self.cleaned_data.get("nombre_usuario") or "").strip().lower()

    def clean(self):
        datos = super().clean()
        if self.cuenta is None and not datos.get("crear"):
            return datos
        nombre = datos.get("nombre_usuario")
        if self.cuenta is None:
            if not nombre:
                self.add_error("nombre_usuario", "Escriba el nombre de usuario.")
            elif not NOMBRE_USUARIO.match(nombre):
                self.add_error(
                    "nombre_usuario",
                    "Use de 3 a 30 caracteres: minúsculas, números, punto, guion o guion bajo.",
                )
            elif Usuario.objects.filter(nombre_usuario=nombre).exists():
                self.add_error("nombre_usuario", "Ese nombre de usuario ya existe.")
        if not datos.get("rol"):
            self.add_error("rol", "RF-03: la cuenta necesita un rol.")
        contrasena, confirmacion = datos.get("contrasena") or "", datos.get("confirmacion") or ""
        if self.cuenta is None and not contrasena:
            self.add_error("contrasena", "Escriba la contraseña inicial.")
        if contrasena:
            if contrasena != confirmacion:
                self.add_error("confirmacion", "La contraseña y su confirmación no coinciden.")
            else:
                try:
                    validate_password(contrasena, Usuario(nombre_usuario=nombre or ""))
                except forms.ValidationError as error:
                    self.add_error("contrasena", error)
        return datos


# --- UI-04 · Catálogo de servicios (S1-11) ------------------------------------
class ServicioForm(forms.ModelForm):
    """UI-04 · Servicio con categoría, precio y duración (RF-04). El puesto se deduce (RD-04)."""

    class Meta:
        model = Servicio
        fields = ["nombre", "categoria", "precio", "duracion_min", "agendable", "activo"]
        labels = {
            "nombre": "Nombre del servicio",
            "categoria": "Categoría",
            "precio": "Precio (MXN)",
            "duracion_min": "Duración (minutos)",
            "agendable": "Se agenda como cita",
            "activo": "Servicio activo",
        }
        help_texts = {
            "precio": "Precio vigente. Los tickets guardan el precio del momento en que se generan (RD-11).",
            "duracion_min": "Entre 5 y 480 minutos, de 5 en 5. Define la hora de fin de la cita.",
            "agendable": "Las aplicaciones se cobran con un servicio que no se agenda (RD-09).",
            "activo": "Un servicio inactivo ya no se ofrece, pero se conserva en citas y tickets anteriores.",
        }
        widgets = {
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}),
            "duracion_min": forms.NumberInput(attrs={"step": "5", "min": "5", "max": "480"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].choices = [("", "Elija la categoría")] + list(CategoriaServicio.choices)
        if not self.instance.pk:
            del self.fields["activo"]
        _estilo(self)

    def is_valid(self):
        valido = super().is_valid()
        _marcar_errores(self)
        return valido

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        repetidos = Servicio.objects.filter(nombre__iexact=nombre, activo=True).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError("Ya existe un servicio activo con ese nombre.")
        return nombre

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        if precio > Decimal("99999.99"):
            raise forms.ValidationError("Revise el precio: es mayor a $99,999.99.")
        return precio

    def clean_duracion_min(self):
        duracion = self.cleaned_data["duracion_min"]
        if not 5 <= duracion <= 480 or duracion % 5:
            raise forms.ValidationError("La duración va de 5 a 480 minutos, en múltiplos de 5.")
        return duracion
