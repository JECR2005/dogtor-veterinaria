"""Componente Catálogos (Tabla 3.2): clientes, mascotas, empleados, servicios, productos y proveedores.

Tablas del diccionario de datos (apartado 3.5): cliente (3.32), especie (3.33), raza (3.34), mascota (3.35),
empleado (3.36), horario_laboral (3.37), servicio (3.39), producto (3.48) y proveedor (3.51).

Convención (D-10): las tablas, llaves, restricciones CHECK e índices se programan en SQL Server
(bd/01_tablas.sql). Estos modelos solo las usan (managed = False) con los mismos nombres de tabla y
columna (db_table / db_column); las opciones (choices) repiten los valores permitidos para los formularios.
"""

from django.db import models
from django.utils import timezone


# --- Valores permitidos -------------------------------------------------------
class PreferenciaContacto(models.TextChoices):
    TELEFONO = "Teléfono", "Teléfono"
    WHATSAPP = "WhatsApp", "WhatsApp"
    CORREO = "Correo", "Correo"


class Sexo(models.TextChoices):
    MACHO = "M", "Macho"
    HEMBRA = "H", "Hembra"


class EstatusMascota(models.TextChoices):
    ACTIVA = "Activa", "Activa"
    INACTIVA = "Inactiva", "Inactiva"
    FALLECIDA = "Fallecida", "Fallecida"


class Puesto(models.TextChoices):
    VETERINARIO = "Veterinario", "Veterinario"
    ESTILISTA = "Estilista", "Estilista"
    RECEPCIONISTA = "Recepcionista", "Recepcionista"
    ADMINISTRADOR = "Administrador", "Administrador"


class DiaSemana(models.IntegerChoices):
    LUNES = 1, "Lunes"
    MARTES = 2, "Martes"
    MIERCOLES = 3, "Miércoles"
    JUEVES = 4, "Jueves"
    VIERNES = 5, "Viernes"
    SABADO = 6, "Sábado"


class CategoriaServicio(models.TextChoices):
    CONSULTA = "Consulta", "Consulta"
    VACUNACION = "Vacunación", "Vacunación"
    DESPARASITACION = "Desparasitación", "Desparasitación"
    PROCEDIMIENTO_MENOR = "Procedimiento menor", "Procedimiento menor"
    ESTETICA = "Estética", "Estética"
    APLICACION = "Aplicación", "Aplicación"


class PuestoRequerido(models.TextChoices):
    VETERINARIO = "Veterinario", "Veterinario"
    ESTILISTA = "Estilista", "Estilista"


class CategoriaProducto(models.TextChoices):
    MEDICAMENTO = "Medicamento", "Medicamento"
    VACUNA = "Vacuna", "Vacuna"
    DESPARASITANTE = "Desparasitante", "Desparasitante"
    ALIMENTO = "Alimento", "Alimento"
    ACCESORIO = "Accesorio", "Accesorio"
    INSUMO = "Insumo", "Insumo"


# --- Tabla 3.32 · CLIENTE -----------------------------------------------------
class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    apellido_paterno = models.CharField(max_length=40)
    apellido_materno = models.CharField(max_length=40, null=True, blank=True)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    preferencia_contacto = models.CharField(max_length=15, choices=PreferenciaContacto.choices)
    rfc = models.CharField(max_length=13, null=True, blank=True)
    razon_social_fiscal = models.CharField(max_length=120, null=True, blank=True)
    regimen_fiscal = models.CharField(max_length=5, null=True, blank=True)
    cp_fiscal = models.CharField(max_length=5, null=True, blank=True)
    acepto_aviso_privacidad = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "cliente"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"


# --- Tabla 3.33 · ESPECIE -----------------------------------------------------
class Especie(models.Model):
    id_especie = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "especie"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return self.nombre


# --- Tabla 3.34 · RAZA --------------------------------------------------------
class Raza(models.Model):
    id_raza = models.AutoField(primary_key=True)
    especie = models.ForeignKey(
        Especie, on_delete=models.PROTECT, db_column="id_especie", related_name="razas"
    )
    nombre = models.CharField(max_length=60)

    class Meta:
        db_table = "raza"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return self.nombre


# --- Tabla 3.35 · MASCOTA -----------------------------------------------------
class Mascota(models.Model):
    id_mascota = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, db_column="id_cliente", related_name="mascotas"
    )
    raza = models.ForeignKey(Raza, on_delete=models.PROTECT, db_column="id_raza", related_name="mascotas")
    nombre = models.CharField(max_length=40)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    peso_actual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    color = models.CharField(max_length=40, null=True, blank=True)
    esterilizado = models.BooleanField(default=False)
    estatus = models.CharField(max_length=10, choices=EstatusMascota.choices, default=EstatusMascota.ACTIVA)

    class Meta:
        db_table = "mascota"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return self.nombre


# --- Tabla 3.36 · EMPLEADO ----------------------------------------------------
class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=80)
    puesto = models.CharField(max_length=15, choices=Puesto.choices)
    cedula_profesional = models.CharField(max_length=12, null=True, blank=True, unique=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "empleado"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} ({self.puesto})"


# --- Tabla 3.37 · HORARIO_LABORAL ---------------------------------------------
class HorarioLaboral(models.Model):
    id_horario = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, db_column="id_empleado", related_name="horarios"
    )
    dia_semana = models.SmallIntegerField(choices=DiaSemana.choices)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    class Meta:
        db_table = "horario_laboral"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.empleado} · {self.get_dia_semana_display()} {self.hora_entrada}-{self.hora_salida}"


# --- Tabla 3.39 · SERVICIO ----------------------------------------------------
class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    categoria = models.CharField(max_length=20, choices=CategoriaServicio.choices)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_min = models.SmallIntegerField()
    puesto_requerido = models.CharField(max_length=15, choices=PuestoRequerido.choices)
    agendable = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "servicio"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return self.nombre


# --- Tabla 3.51 · PROVEEDOR ---------------------------------------------------
class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    razon_social = models.CharField(max_length=120)
    rfc = models.CharField(max_length=13, null=True, blank=True, unique=True)
    contacto = models.CharField(max_length=80, null=True, blank=True)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(max_length=100, null=True, blank=True)
    condiciones_pago = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "proveedor"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return self.razon_social


# --- Tabla 3.48 · PRODUCTO ----------------------------------------------------
class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_proveedor",
        related_name="productos",
    )
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CategoriaProducto.choices)
    unidad_medida = models.CharField(max_length=15)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_minimo = models.IntegerField(default=0)
    requiere_receta = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "producto"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"
