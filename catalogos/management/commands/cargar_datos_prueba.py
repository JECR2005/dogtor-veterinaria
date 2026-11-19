"""S0-19 · Carga datos FICTICIOS repetibles para desarrollo y pruebas.

Justificación: la cláusula Undécima prohíbe usar datos reales de clientes en las pruebas; las pruebas de
aceptación necesitan siempre los mismos datos, y la prueba de carga de RNF-05 pide más de 1,000 mascotas
(apartado 4.5.1, "Datos").

Uso:
    python manage.py cargar_datos_prueba                 # 50 mascotas
    python manage.py cargar_datos_prueba --mascotas 1200 # para la prueba de carga (RNF-05)

Es idempotente: los catálogos se crean una sola vez y solo se agregan las mascotas que falten para llegar
a la cantidad pedida. Se niega a correr en producción.
"""

import os
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogos.models import (
    CategoriaProducto,
    CategoriaServicio,
    Cliente,
    DiaSemana,
    Empleado,
    Especie,
    EstatusMascota,
    HorarioLaboral,
    Mascota,
    PreferenciaContacto,
    Producto,
    Proveedor,
    Puesto,
    PuestoRequerido,
    Raza,
    Servicio,
    Sexo,
)
from clinico.models import ExpedienteClinico
from inventario.models import (
    DetallePedido,
    EstadoPedido,
    Lote,
    MovimientoInventario,
    PedidoCompra,
    TipoMovimiento,
)
from seguridad.models import Rol, Usuario

REFERENCIA = "DATOS-PRUEBA"

RAZAS = {
    "Perro": [
        "Mestizo",
        "Labrador Retriever",
        "Chihuahua",
        "Pastor Alemán",
        "Poodle",
        "Schnauzer",
        "Golden Retriever",
        "Pug",
        "Yorkshire Terrier",
        "Bulldog Francés",
    ],
    "Gato": ["Mestizo", "Siamés", "Persa", "Maine Coon", "Angora"],
}

# (nombre, apellidos, puesto, cédula ficticia, usuario)
EMPLEADOS = [
    ("Laura", "Medina Ficticia", Puesto.VETERINARIO, "FICT0000001", "veterinario"),
    ("Mario", "Estrada Ficticio", Puesto.ESTILISTA, None, "estilista"),
    ("Sofía", "Reyes Ficticia", Puesto.RECEPCIONISTA, None, "recepcion"),
    ("Andrés", "Duarte Ficticio", Puesto.ADMINISTRADOR, None, "administrador"),
]

# (nombre, categoría, precio, duración en min, puesto, agendable) · precios del apartado 1.8.1
SERVICIOS = [
    ("Consulta general", CategoriaServicio.CONSULTA, "400.00", 30, PuestoRequerido.VETERINARIO, True),
    ("Vacunación", CategoriaServicio.VACUNACION, "350.00", 20, PuestoRequerido.VETERINARIO, True),
    ("Desparasitación", CategoriaServicio.DESPARASITACION, "350.00", 15, PuestoRequerido.VETERINARIO, True),
    (
        "Curación menor",
        CategoriaServicio.PROCEDIMIENTO_MENOR,
        "600.00",
        45,
        PuestoRequerido.VETERINARIO,
        True,
    ),
    ("Baño", CategoriaServicio.ESTETICA, "350.00", 60, PuestoRequerido.ESTILISTA, True),
    ("Corte y estética", CategoriaServicio.ESTETICA, "450.00", 90, PuestoRequerido.ESTILISTA, True),
    ("Spa", CategoriaServicio.ESTETICA, "500.00", 90, PuestoRequerido.ESTILISTA, True),
    # RD-09: servicios con los que se cobran las aplicaciones; no se agendan y no descuentan stock
    ("Aplicación de vacuna", CategoriaServicio.APLICACION, "350.00", 10, PuestoRequerido.VETERINARIO, False),
    (
        "Aplicación de desparasitante",
        CategoriaServicio.APLICACION,
        "350.00",
        10,
        PuestoRequerido.VETERINARIO,
        False,
    ),
]

# (razón social, condiciones de pago, RFC, contacto, correo). Todo inventado (cláusula Undécima).
PROVEEDORES = [
    (
        "Distribuidora Veterinaria del Golfo (ficticia)",
        "Crédito a 30 días",
        "DVG200115KX1",
        "Laura Méndez",
        "ventas@dvg.example.com",
    ),
    (
        "Alimentos para Mascotas Huasteca (ficticia)",
        "Contado",
        "AMH190320LM2",
        "Óscar Treviño",
        "pedidos@amh.example.com",
    ),
    (
        "Insumos de Estética Madero (ficticia)",
        "Crédito a 15 días",
        "IEM210907QR3",
        "Rocío Salinas",
        "contacto@iem.example.com",
    ),
]

# (código, nombre, categoría, unidad, precio, stock mínimo, requiere receta, índice de proveedor)
PRODUCTOS = [
    ("VAC-001", "Vacuna múltiple canina", CategoriaProducto.VACUNA, "Dosis", "180.00", 10, False, 0),
    ("VAC-002", "Vacuna antirrábica", CategoriaProducto.VACUNA, "Dosis", "120.00", 10, False, 0),
    ("VAC-003", "Vacuna triple felina", CategoriaProducto.VACUNA, "Dosis", "190.00", 5, False, 0),
    (
        "DES-001",
        "Desparasitante interno tabletas",
        CategoriaProducto.DESPARASITANTE,
        "Tableta",
        "60.00",
        20,
        False,
        0,
    ),
    (
        "MED-001",
        "Amoxicilina 250 mg tabletas",
        CategoriaProducto.MEDICAMENTO,
        "Tableta",
        "15.00",
        30,
        True,
        0,
    ),
    ("MED-002", "Meloxicam suspensión 10 mL", CategoriaProducto.MEDICAMENTO, "Frasco", "210.00", 5, True, 0),
    ("ALI-001", "Croquetas perro adulto 2 kg", CategoriaProducto.ALIMENTO, "Bolsa", "320.00", 8, False, 1),
    ("ALI-002", "Croquetas gato adulto 1.5 kg", CategoriaProducto.ALIMENTO, "Bolsa", "290.00", 8, False, 1),
    ("ACC-001", "Collar ajustable mediano", CategoriaProducto.ACCESORIO, "Pieza", "150.00", 5, False, 1),
    ("INS-001", "Shampoo hipoalergénico 1 L", CategoriaProducto.INSUMO, "Botella", "240.00", 4, False, 2),
    # Se aplica por mL: sus existencias llevan decimales (D-04)
    (
        "MED-003",
        "Ivermectina solución inyectable 1 %",
        CategoriaProducto.MEDICAMENTO,
        "mL",
        "8.00",
        20,
        True,
        0,
    ),
]

# S2-03 · Lotes de cada producto: (sufijo, días para caducar o None si no caduca, cantidad).
# Los productos que no aparecen tienen dos lotes vigentes sin alerta. Escenarios de P2 (RF-11, RD-03, RD-05):
LOTES = {
    # Caduca en menos de 30 días (alerta), uno vigente después y uno vencido que no debe ofrecerse (RD-03);
    # al descontar se toma primero el A, que caduca antes (RD-05, TU-08)
    "VAC-001": [("A", 15, 6), ("B", 200, 20), ("V", -10, 4)],
    "VAC-003": [
        ("A", 200, 3)
    ],  # 3 de un mínimo de 5: alerta de stock bajo; se repone con el pedido pendiente
    "MED-001": [("A", 25, 20), ("B", 180, 40)],  # caduca en menos de 30 días
    "ALI-002": [],  # sin existencias: alerta de stock bajo
    "ACC-001": [("A", None, 12)],  # no caduca
    "MED-003": [("A", 250, "100.00")],  # en mL; después se ajusta -2.50 (ver AJUSTES)
}

# (código, número de lote, cantidad con signo, motivo): ajustes de inventario con motivo (R08, D-04)
AJUSTES = [("MED-003", "MED-003-A", "-2.50", "Se derramó al cargar la jeringa")]

# S2-03 · Pedidos de compra: (proveedor, estado, días desde el pedido, [(código, cantidad, costo unitario)]).
# El primero es el que se recibe en la aceptación de P2 (TA-03): repone VAC-003 y MED-001.
PEDIDOS = [
    (0, EstadoPedido.PENDIENTE, 2, [("VAC-003", 20, "140.00"), ("MED-001", 60, "9.00")]),
    (1, EstadoPedido.PENDIENTE, 1, [("ALI-002", 10, "210.00")]),
    (2, EstadoPedido.CANCELADO, 12, [("INS-001", 5, "150.00")]),
]

NOMBRES = [
    "Ana",
    "Luis",
    "María",
    "José",
    "Carmen",
    "Jorge",
    "Patricia",
    "Miguel",
    "Rosa",
    "Juan",
    "Elena",
    "Ricardo",
    "Daniela",
    "Fernando",
    "Gabriela",
    "Héctor",
    "Lucía",
    "Raúl",
    "Verónica",
    "Óscar",
]
APELLIDOS = [
    "García",
    "Hernández",
    "Martínez",
    "López",
    "González",
    "Pérez",
    "Rodríguez",
    "Sánchez",
    "Ramírez",
    "Cruz",
    "Flores",
    "Gómez",
    "Morales",
    "Vázquez",
    "Reyes",
    "Jiménez",
    "Torres",
    "Ruiz",
]
NOMBRES_MASCOTA = [
    "Max",
    "Luna",
    "Rocky",
    "Canela",
    "Toby",
    "Nala",
    "Firulais",
    "Kira",
    "Bruno",
    "Mia",
    "Coco",
    "Lola",
    "Simba",
    "Pelusa",
    "Zeus",
    "Michi",
    "Chispa",
    "Oreo",
    "Thor",
    "Frida",
]
COLORES = ["Negro", "Blanco", "Café", "Dorado", "Gris", "Atigrado", "Manchado", "Crema"]


class Command(BaseCommand):
    help = "Carga datos ficticios repetibles (cláusula Undécima: nunca datos reales)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mascotas", type=int, default=50, help="Total de mascotas que debe haber (defecto 50)."
        )
        parser.add_argument(
            "--semilla", type=int, default=2026, help="Semilla para que los datos sean repetibles."
        )

    def handle(self, *args, **opciones):
        if not getattr(settings, "DOGTOR_PERMITIR_DATOS_PRUEBA", False):
            raise CommandError("Este comando no se ejecuta en producción (cláusula Undécima).")
        if opciones["mascotas"] < 0:
            raise CommandError("--mascotas debe ser 0 o mayor.")

        azar = random.Random(opciones["semilla"])
        hoy = timezone.localdate()
        contrasena = os.environ.get("DATOS_PRUEBA_CONTRASENA", "Dogtor-Prueba-2026")

        with transaction.atomic():
            razas = self._especies_y_razas()
            empleados = self._empleados_y_usuarios(hoy, contrasena)
            self._servicios()
            self._productos_y_lotes(hoy, empleados[Puesto.ADMINISTRADOR])
            nuevas = self._clientes_y_mascotas(azar, razas, opciones["mascotas"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos ficticios listos: {Mascota.objects.count()} mascotas ({nuevas} nuevas), "
                f"{Cliente.objects.count()} clientes, {Producto.objects.count()} productos, "
                f"{Usuario.objects.count()} cuentas."
            )
        )
        if nuevas:
            self.stdout.write(
                "Cuentas: administrador, veterinario, estilista y recepcion "
                "(contraseña en DATOS_PRUEBA_CONTRASENA del archivo .env)."
            )

    # --- Catálogos ------------------------------------------------------------
    def _especies_y_razas(self):
        razas = []
        for especie_nombre, nombres in RAZAS.items():
            especie, _ = Especie.objects.get_or_create(nombre=especie_nombre)
            for nombre in nombres:
                raza, _ = Raza.objects.get_or_create(especie=especie, nombre=nombre)
                razas.append(raza)
        return razas

    def _empleados_y_usuarios(self, hoy, contrasena):
        por_puesto = {}
        for nombre, apellidos, puesto, cedula, nombre_usuario in EMPLEADOS:
            empleado, creado = Empleado.objects.get_or_create(
                nombre=nombre,
                apellidos=apellidos,
                defaults={
                    "puesto": puesto,
                    "cedula_profesional": cedula,
                    "fecha_ingreso": hoy - timedelta(days=90),
                },
            )
            if creado:
                # Horario de atención: lunes a sábado de 9:00 a 19:00 h (RNF-06, RD-02)
                HorarioLaboral.objects.bulk_create(
                    HorarioLaboral(
                        empleado=empleado, dia_semana=dia, hora_entrada=time(9), hora_salida=time(19)
                    )
                    for dia in DiaSemana.values
                )
            if not Usuario.objects.filter(nombre_usuario=nombre_usuario).exists():
                Usuario.objects.create_user(
                    nombre_usuario, contrasena, empleado=empleado, rol=Rol(puesto.value)
                )
            por_puesto[puesto] = empleado
        return por_puesto

    def _servicios(self):
        for nombre, categoria, precio, duracion, puesto, agendable in SERVICIOS:
            Servicio.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "categoria": categoria,
                    "precio": Decimal(precio),
                    "duracion_min": duracion,
                    "puesto_requerido": puesto,
                    "agendable": agendable,
                },
            )

    def _productos_y_lotes(self, hoy, administrador):
        proveedores = []
        for i, (razon_social, condiciones, rfc, contacto, correo) in enumerate(PROVEEDORES, start=1):
            proveedor, _ = Proveedor.objects.get_or_create(
                razon_social=razon_social,
                defaults={
                    "telefono": f"833000000{i}",
                    "condiciones_pago": condiciones,
                    "rfc": rfc,
                    "contacto": contacto,
                    "correo": correo,
                },
            )
            proveedores.append(proveedor)

        productos = {}
        for codigo, nombre, categoria, unidad, precio, minimo, receta, i_prov in PRODUCTOS:
            producto, creado = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "categoria": categoria,
                    "unidad_medida": unidad,
                    "precio_venta": Decimal(precio),
                    "stock_minimo": minimo,
                    "requiere_receta": receta,
                    "proveedor": proveedores[i_prov],
                },
            )
            productos[codigo] = producto
            if creado:
                lotes = LOTES.get(codigo, [("A", 150, minimo * 2), ("B", 300, minimo * 2)])
                self._lotes(producto, lotes, hoy, administrador)

        for codigo, numero, cantidad, motivo in AJUSTES:
            lote = Lote.objects.filter(producto=productos[codigo], numero_lote=numero).first()
            if lote is None or lote.movimientos.filter(tipo=TipoMovimiento.AJUSTE).exists():
                continue
            MovimientoInventario.objects.create(
                lote=lote,
                empleado=administrador,
                tipo=TipoMovimiento.AJUSTE,
                cantidad=Decimal(cantidad),
                motivo=motivo,
                referencia=REFERENCIA,
            )
            lote.cantidad_disponible += Decimal(cantidad)
            lote.save(update_fields=["cantidad_disponible"])

        self._pedidos(proveedores, productos, hoy, administrador)

    def _lotes(self, producto, lotes, hoy, administrador):
        for sufijo, dias, cantidad in lotes:
            cantidad = Decimal(cantidad)
            lote = Lote.objects.create(
                producto=producto,
                numero_lote=f"{producto.codigo}-{sufijo}",
                fecha_caducidad=None if dias is None else hoy + timedelta(days=dias),
                cantidad_disponible=cantidad,
                fecha_entrada=hoy - timedelta(days=30),
            )
            MovimientoInventario.objects.create(
                lote=lote,
                empleado=administrador,
                tipo=TipoMovimiento.ENTRADA,
                cantidad=cantidad,
                referencia=REFERENCIA,
            )

    def _pedidos(self, proveedores, productos, hoy, administrador):
        for i_prov, estado, dias, partidas in PEDIDOS:
            proveedor = proveedores[i_prov]
            if PedidoCompra.objects.filter(proveedor=proveedor, estado=estado).exists():
                continue
            pedido = PedidoCompra.objects.create(
                proveedor=proveedor,
                empleado=administrador,
                fecha_pedido=hoy - timedelta(days=dias),
                estado=estado,
                total=sum(cantidad * Decimal(costo) for _, cantidad, costo in partidas),
            )
            DetallePedido.objects.bulk_create(
                DetallePedido(
                    pedido=pedido,
                    producto=productos[codigo],
                    cantidad_solicitada=cantidad,
                    costo_unitario=Decimal(costo),
                )
                for codigo, cantidad, costo in partidas
            )

    # --- Clientes y mascotas --------------------------------------------------
    def _clientes_y_mascotas(self, azar, razas, total_mascotas):
        faltan = total_mascotas - Mascota.objects.count()
        if faltan <= 0:
            return 0

        base = Cliente.objects.count()
        por_cliente = []
        while sum(por_cliente) < faltan:
            por_cliente.append(min(azar.choice([1, 1, 1, 2, 2, 3]), faltan - sum(por_cliente)))

        # Se crean uno por uno: en SQL Server, bulk_create no devuelve las llaves generadas por defecto
        # (opción return_rows_bulk_insert de mssql-django) y las mascotas y expedientes las necesitan.
        creadas = 0
        for i, cantidad in enumerate(por_cliente, start=base + 1):
            preferencia = azar.choice(PreferenciaContacto.values)
            cliente = Cliente.objects.create(
                nombre=azar.choice(NOMBRES),
                apellido_paterno=azar.choice(APELLIDOS),
                apellido_materno=azar.choice(APELLIDOS),
                telefono=f"833{i:07d}",
                correo=f"cliente{i}@example.com" if preferencia == PreferenciaContacto.CORREO else None,
                direccion=f"Calle Ficticia {i}, Tampico, Tamps.",
                preferencia_contacto=preferencia,
                acepto_aviso_privacidad=True,
            )
            for _ in range(cantidad):
                mascota = Mascota.objects.create(
                    cliente=cliente,
                    raza=azar.choice(razas),
                    nombre=azar.choice(NOMBRES_MASCOTA),
                    sexo=azar.choice(Sexo.values),
                    fecha_nacimiento=date(2015, 1, 1) + timedelta(days=azar.randint(0, 365 * 10)),
                    peso_actual=Decimal(azar.randint(150, 4000)) / 100,
                    color=azar.choice(COLORES),
                    esterilizado=azar.random() < 0.5,
                    estatus=EstatusMascota.ACTIVA,
                )
                # RD-10: cada mascota tiene un único expediente clínico
                ExpedienteClinico.objects.create(mascota=mascota)
                creadas += 1
        return creadas
