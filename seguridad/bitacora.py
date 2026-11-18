"""S1-07 · Servicio de bitácora de auditoría (RNF-03, Tabla 3.57).

Registra quién, cuándo, qué acción, sobre qué registro y con qué valores previos. Lo usan los servicios
que cambian datos sensibles: bajas de clientes y reactivaciones de cuentas en P1; ventas, consultas,
recetas e inventario en P2 a P4; exportaciones en P5.

Reglas de uso:
- Se llama dentro de la misma transacción que el cambio (`transaction.atomic`): si la bitácora falla,
  el cambio se revierte, y no queda un cambio sin su registro.
- Los valores previos se toman ANTES de modificar el registro, con `valores_de(instancia)`.
- Nunca se guardan contraseñas ni su hash.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from .models import AccionBitacora, BitacoraAuditoria

# Campos que jamás se copian a la bitácora, aunque cambien
CAMPOS_EXCLUIDOS = frozenset({"password", "hash_contrasena"})


def valores_de(instancia, campos=None):
    """Valores actuales de un registro, por nombre de columna, listos para guardarse como previos."""
    valores = {}
    for campo in instancia._meta.concrete_fields:
        if campo.name in CAMPOS_EXCLUIDOS or campo.column in CAMPOS_EXCLUIDOS:
            continue
        if campos is not None and campo.name not in campos and campo.attname not in campos:
            continue
        valores[campo.column] = getattr(instancia, campo.attname)
    return valores


def _a_texto(valores):
    if valores is None:
        return None
    return json.dumps(valores, cls=DjangoJSONEncoder, ensure_ascii=False, sort_keys=True)


def registrar(usuario, accion, instancia, valores_previos=None, entidad=None):
    """Crea el registro de bitácora. `accion` es un valor de AccionBitacora."""
    if accion not in AccionBitacora.values:
        raise ValueError(f"Acción de bitácora desconocida: {accion}")
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("La bitácora se registra dentro de la transacción del cambio (RNF-03).")
    return BitacoraAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad or instancia._meta.db_table,
        id_registro=instancia.pk,
        valores_previos=_a_texto(valores_previos),
    )


def valores_previos(registro):
    """Lee los valores previos guardados (para la consulta y exportación de P5)."""
    return json.loads(registro.valores_previos) if registro.valores_previos else None
