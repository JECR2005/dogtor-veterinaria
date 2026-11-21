"""S1-07 · Servicio de bitácora de auditoría (RNF-03, Tabla 3.57).

Registra quién, cuándo, qué acción, sobre qué registro y con qué valores previos. Lo usan los servicios
que cambian datos sensibles: bajas de clientes y reactivaciones de cuentas en P1; ventas, consultas,
recetas e inventario desde P5 (S5-04); exportaciones de la bitácora y de contactos (S5-05, S5-06).

Reglas de uso:
- Se llama dentro de la misma transacción que el cambio (`transaction.atomic`): si la bitácora falla,
  el cambio se revierte, y no queda un cambio sin su registro.
- Los valores previos se toman ANTES de modificar el registro, con `valores_de(instancia)`.
- Nunca se guardan contraseñas ni su hash.
- Quien actúa puede llegar como cuenta (Usuario) o como empleado: se registra la cuenta del empleado, porque
  toda acción en el sistema la hace una cuenta (Tabla 3.38).
- La base no deja modificar ni borrar un registro de la bitácora (TR_bitacora_inmutable, D-23).
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from .models import AccionBitacora, BitacoraAuditoria, Usuario

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


def cuenta_de(quien):
    """La cuenta que hizo el cambio: la misma si ya es una cuenta, o la del empleado."""
    if isinstance(quien, Usuario):
        return quien
    try:
        return quien.usuario
    except Usuario.DoesNotExist:
        raise RuntimeError(
            f"«{quien}» no tiene cuenta: la bitácora necesita la cuenta que hizo el cambio (RNF-03)."
        ) from None


def _validar(accion):
    if accion not in AccionBitacora.values:
        raise ValueError(f"Acción de bitácora desconocida: {accion}")
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("La bitácora se registra dentro de la transacción del cambio (RNF-03).")


def registrar(usuario, accion, instancia, valores_previos=None, entidad=None):
    """Crea el registro de bitácora. `accion` es un valor de AccionBitacora; `usuario`, cuenta o empleado."""
    _validar(accion)
    return BitacoraAuditoria.objects.create(
        usuario=cuenta_de(usuario),
        accion=accion,
        entidad=entidad or instancia._meta.db_table,
        id_registro=instancia.pk,
        valores_previos=_a_texto(valores_previos),
    )


def registrar_exportacion(usuario, entidad, detalle):
    """S5-05 y S5-06 · Una exportación no cambia registros: se guarda qué se exportó (filtros y número de
    filas) en lugar de valores previos, con id_registro 0 (D-23)."""
    _validar(AccionBitacora.EXPORTACION)
    return BitacoraAuditoria.objects.create(
        usuario=cuenta_de(usuario),
        accion=AccionBitacora.EXPORTACION,
        entidad=entidad,
        id_registro=0,
        valores_previos=_a_texto(detalle),
    )


def registros_de(instancia, entidad=None):
    """Registros de bitácora de un registro (por ejemplo, las correcciones de una consulta)."""
    return BitacoraAuditoria.objects.filter(
        entidad=entidad or instancia._meta.db_table, id_registro=instancia.pk
    )


def valores_previos(registro):
    """Lee los valores previos guardados (para la consulta y exportación de P5)."""
    return json.loads(registro.valores_previos) if registro.valores_previos else None


# --- S5-05 · Consulta y exportación (UI-20) ---------------------------------------------
# Nombre legible de cada tabla que aparece en la bitácora (las exportaciones usan su propia entidad)
ENTIDADES = {
    "venta": "Ticket",
    "pago": "Pago",
    "consulta": "Consulta",
    "aplicacion": "Aplicación",
    "receta": "Receta",
    "registro_estetica": "Atención de estética",
    "lote": "Lote (ajuste)",
    "movimiento_inventario": "Entrada de inventario",
    "pedido_compra": "Pedido de compra",
    "cliente": "Cliente",
    "usuario": "Cuenta",
    "bitacora_auditoria": "Bitácora",
    "contactos": "Contactos de clientes",
}

COLUMNAS_CSV = [
    "Fecha y hora",
    "Usuario",
    "Empleado",
    "Acción",
    "Qué",
    "Registro",
    "Valores previos o detalle",
]


def nombre_de_entidad(entidad):
    return ENTIDADES.get(entidad, entidad)


def buscar(desde, hasta, usuario=None, accion="", entidad=""):
    """Registros del periodo (fechas locales, inclusive), del más reciente al más antiguo."""
    from datetime import datetime, time, timedelta

    from django.utils import timezone

    inicio = timezone.make_aware(datetime.combine(desde, time.min))
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min))
    registros = BitacoraAuditoria.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=fin)
    if usuario is not None:
        registros = registros.filter(usuario=usuario)
    if accion:
        registros = registros.filter(accion=accion)
    if entidad:
        registros = registros.filter(entidad=entidad)
    return registros.select_related("usuario__empleado").order_by("-fecha_hora", "-id_bitacora")


def fila_csv(registro):
    from django.utils import timezone

    empleado = registro.usuario.empleado
    return [
        timezone.localtime(registro.fecha_hora).strftime("%d/%m/%Y %H:%M:%S"),
        registro.usuario.nombre_usuario,
        f"{empleado.nombre} {empleado.apellidos}",
        registro.accion,
        nombre_de_entidad(registro.entidad),
        registro.id_registro or "",
        registro.valores_previos or "",
    ]
