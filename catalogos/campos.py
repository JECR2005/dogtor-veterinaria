"""S5 · Recomendaciones de QA: validaciones de entrada comunes a todos los formularios.

- `DecimalSinExponente`: un número escrito con la letra «e» (notación científica, «1e2» = 100) se rechaza. El
  navegador deja escribir «e» en los campos numéricos y Django la aceptaría; en pantalla tampoco se puede
  escribir (static/js/numeros.js), pero el servidor es el que decide.
- `validar_nombre`: nombres y apellidos de personas y nombres de mascotas solo con letras (con acentos, ü
  y ñ), espacios, apóstrofo, guion y punto; sin números ni otros símbolos, y con al menos 2 letras.
"""

import re

from django import forms
from django.core.exceptions import ValidationError

MENSAJE_EXPONENTE = (
    "Escriba la cantidad solo con números y punto decimal, sin la letra «e» (por ejemplo, 12.50)."
)
MENSAJE_NOMBRE = (
    "Escriba {que} solo con letras; se permiten acentos, ñ, espacios, apóstrofo ('), guion (-) y punto (.). "
    "No lleva números."
)
MENSAJE_LETRAS = "Escriba al menos 2 letras en {que}."
SIGNOS_PERMITIDOS = set(" '’-.")


class DecimalSinExponente(forms.DecimalField):
    """DecimalField que no acepta notación científica («1e2», «2E-1»)."""

    default_error_messages = {"exponente": MENSAJE_EXPONENTE}

    def to_python(self, value):
        if isinstance(value, str) and re.search(r"[eE]", value):
            raise ValidationError(self.error_messages["exponente"], code="exponente")
        return super().to_python(value)


def validar_nombre(valor, que="el nombre", obligatorio=True):
    """Limpia espacios repetidos y valida el nombre; devuelve el texto limpio o None si está vacío."""
    texto = " ".join((valor or "").split())
    if not texto:
        if obligatorio:
            raise ValidationError("Este campo es obligatorio.", code="required")
        return None
    if any(not (letra.isalpha() or letra in SIGNOS_PERMITIDOS) for letra in texto):
        raise ValidationError(MENSAJE_NOMBRE.format(que=que), code="caracteres")
    if not texto[0].isalpha():
        raise ValidationError(MENSAJE_NOMBRE.format(que=que), code="caracteres")
    if sum(letra.isalpha() for letra in texto) < 2:
        raise ValidationError(MENSAJE_LETRAS.format(que=que), code="letras")
    return texto
