"""Formato local de México (RI-13): importes en pesos con separador de miles, por ejemplo $1,250.00.

Uso en plantillas: {% load formato %} ... {{ servicio.precio|pesos }} · {{ servicio.duracion_min|duracion }}
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def pesos(valor):
    if valor in (None, ""):
        return "—"
    try:
        cantidad = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return valor
    signo = "-" if cantidad < 0 else ""
    return f"{signo}${abs(cantidad):,.2f}"


@register.filter
def duracion(minutos):
    """45 → «45 min»; 90 → «1 h 30 min»; 60 → «1 h»."""
    if minutos in (None, ""):
        return "—"
    horas, resto = divmod(int(minutos), 60)
    if not horas:
        return f"{resto} min"
    return f"{horas} h {resto} min" if resto else f"{horas} h"
