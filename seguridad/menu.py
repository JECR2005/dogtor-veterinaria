"""Menú de opciones por rol (apartado 4.4, Tablas 4.8 y 4.9).

Es la fuente única de los permisos de pantalla: con él se construye el menú lateral y se valida el
permiso en cada solicitud (RNF-01, mínimo privilegio). No depende de Django para poder probarse solo.
"""

NIVEL_COMPLETO = "completo"  # ● en la Tabla 4.9
NIVEL_CONSULTA = "consulta"  # ○ en la Tabla 4.9

ADMIN, VET, EST, REC = "Administrador", "Veterinario", "Estilista", "Recepcionista"
C, R = NIVEL_COMPLETO, NIVEL_CONSULTA

# (clave, etiqueta, icono Bootstrap Icons, submenú, {rol: nivel})  · Tabla 4.8 y Tabla 4.9
OPCIONES = [
    ("inicio", "Inicio", "house", ["Panel del día"], {ADMIN: C, VET: C, EST: C, REC: C}),
    (
        "agenda",
        "Agenda",
        "calendar-week",
        ["Calendario", "Nueva cita", "Reprogramar o cancelar"],
        {ADMIN: R, VET: R, EST: R, REC: C},
    ),
    (
        "clientes",
        "Clientes y mascotas",
        "people",
        ["Clientes", "Mascotas", "Exportar contactos"],
        {ADMIN: R, VET: R, EST: R, REC: C},
    ),
    (
        "consulta",
        "Consulta clínica",
        "clipboard2-pulse",
        ["Consultas del día", "Historial de la mascota", "Aplicaciones", "Recetas"],
        {ADMIN: R, VET: C},
    ),
    (
        "estetica",
        "Estética",
        "scissors",
        ["Mi agenda de estética", "Registrar atención"],
        {ADMIN: R, VET: R, EST: C},
    ),
    ("recordatorios", "Recordatorios", "bell", ["Lista del día"], {ADMIN: R, REC: C}),
    (
        "ventas",
        "Ventas y caja",
        "cash-coin",
        ["Nuevo ticket", "Tickets", "Cancelar venta", "Corte de caja"],
        {ADMIN: C, REC: C},
    ),
    ("inventario", "Inventario", "box-seam", ["Productos y lotes", "Alertas"], {ADMIN: C}),
    ("compras", "Compras", "truck", ["Proveedores", "Pedidos", "Recibir pedido"], {ADMIN: C}),
    (
        "administracion",
        "Administración",
        "gear",
        ["Empleados y usuarios", "Catálogo de servicios"],
        {ADMIN: C},
    ),
    ("bitacora", "Bitácora", "journal-text", ["Consultar", "Exportar"], {ADMIN: C}),
    (
        "cuenta",
        "Mi cuenta",
        "person-circle",
        ["Cambiar contraseña", "Cerrar sesión"],
        {ADMIN: C, VET: C, EST: C, REC: C},
    ),
]

ROLES = (ADMIN, VET, EST, REC)


def nivel_de_acceso(rol, clave):
    """Nivel de acceso de un rol a una opción, o None si no tiene acceso."""
    for opcion_clave, _etiqueta, _icono, _submenu, accesos in OPCIONES:
        if opcion_clave == clave:
            return accesos.get(rol)
    raise KeyError(f"Opción de menú desconocida: {clave}")


def opciones_para(rol):
    """Opciones del menú lateral que ve un rol, en el orden de la Tabla 4.8."""
    return [
        {"clave": clave, "etiqueta": etiqueta, "icono": icono, "submenu": submenu, "nivel": accesos[rol]}
        for clave, etiqueta, icono, submenu, accesos in OPCIONES
        if rol in accesos
    ]
