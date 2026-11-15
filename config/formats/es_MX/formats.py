"""RI-13 · Formato local de México para todo el sistema (S1-17).

Fechas día/mes/año, hora de 24 horas e importes con separador de miles (por ejemplo $1,250.00).
Django usa estos formatos cuando una plantilla muestra una fecha, hora o número sin formato explícito.
"""

DATE_FORMAT = "d/m/Y"
SHORT_DATE_FORMAT = "d/m/Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"
MONTH_DAY_FORMAT = "j \\d\\e F"
YEAR_MONTH_FORMAT = "F \\d\\e Y"
FIRST_DAY_OF_WEEK = 1  # lunes

DATE_INPUT_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]  # el primero es el de <input type="date">
TIME_INPUT_FORMATS = ["%H:%M", "%H:%M:%S"]
DATETIME_INPUT_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]

DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = ","
NUMBER_GROUPING = 3
