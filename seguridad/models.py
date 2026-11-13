"""Componente Seguridad y acceso (Tabla 3.2): usuarios, roles y bitácora de auditoría.

Tablas del diccionario de datos: usuario (3.38) y bitacora_auditoria (3.57).

S0-13: el usuario propio se define ANTES de la primera migración. Django exige fijar AUTH_USER_MODEL
desde el inicio; cambiarlo después obliga a rehacer la base de datos.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from .menu import NIVEL_COMPLETO, NIVEL_CONSULTA, nivel_de_acceso


class Rol(models.TextChoices):
    ADMINISTRADOR = "Administrador", "Administrador"
    VETERINARIO = "Veterinario", "Veterinario"
    ESTILISTA = "Estilista", "Estilista"
    RECEPCIONISTA = "Recepcionista", "Recepcionista"


class AccionBitacora(models.TextChoices):
    ALTA = "Alta", "Alta"
    MODIFICACION = "Modificación", "Modificación"
    CANCELACION = "Cancelación", "Cancelación"
    BAJA_LOGICA = "Baja lógica", "Baja lógica"
    EXPORTACION = "Exportación", "Exportación"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, nombre_usuario, password=None, **campos):
        if not nombre_usuario:
            raise ValueError("La cuenta necesita un nombre de usuario.")
        if not campos.get("rol"):
            raise ValueError("RF-03: no se puede crear una cuenta sin rol.")
        usuario = self.model(nombre_usuario=nombre_usuario, **campos)
        usuario.set_password(password)  # hash con sal; nunca texto plano (RNF-01)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, nombre_usuario, password=None, **campos):
        """Cuenta inicial del Administrador (`python manage.py createsuperuser`).

        Toda cuenta pertenece a un empleado (Tabla 3.38). Si no se indica, se crea el empleado
        Administrador; después se completan sus datos desde Administración > Empleados y usuarios.
        """
        from catalogos.models import Empleado, Puesto

        campos.setdefault("rol", Rol.ADMINISTRADOR)
        if campos["rol"] != Rol.ADMINISTRADOR:
            raise ValueError("La cuenta inicial debe tener rol Administrador.")
        if "empleado" not in campos and "empleado_id" not in campos:
            campos["empleado"] = Empleado.objects.create(
                nombre=nombre_usuario,
                apellidos="(cuenta inicial)",
                puesto=Puesto.ADMINISTRADOR,
                fecha_ingreso=timezone.localdate(),
            )
        return self.create_user(nombre_usuario, password, **campos)


# --- Tabla 3.38 · USUARIO -----------------------------------------------------
class Usuario(AbstractBaseUser):
    id_usuario = models.AutoField(primary_key=True)
    empleado = models.OneToOneField(
        "catalogos.Empleado", on_delete=models.PROTECT, db_column="id_empleado", related_name="usuario"
    )
    nombre_usuario = models.CharField(max_length=30, unique=True)
    # Se sobrescriben los campos de AbstractBaseUser para usar los nombres y tamaños del diccionario
    password = models.CharField("contraseña", max_length=255, db_column="hash_contrasena")
    rol = models.CharField(max_length=15, choices=Rol.choices)
    activo = models.BooleanField(default=True)
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    last_login = models.DateTimeField("último acceso", null=True, blank=True, db_column="ultimo_acceso")

    objects = UsuarioManager()

    USERNAME_FIELD = "nombre_usuario"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "usuario"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.nombre_usuario} ({self.rol})"

    # Django consulta is_active para permitir o negar el acceso; se toma del campo «activo».
    @property
    def is_active(self):
        return self.activo

    @property
    def esta_bloqueado(self):
        """RNF-01: la cuenta se bloquea al quinto intento fallido (la lógica de conteo se programa en P1)."""
        from django.conf import settings

        return self.intentos_fallidos >= getattr(settings, "DOGTOR_INTENTOS_MAXIMOS", 5)

    def tiene_permiso(self, opcion, nivel=NIVEL_CONSULTA):
        """Usuario.tienePermiso del diagrama de clases: aplica la Tabla 4.9 con mínimo privilegio.

        `opcion` es la clave de una opción del menú (por ejemplo "ventas") y `nivel` es
        NIVEL_CONSULTA o NIVEL_COMPLETO.
        """
        if not self.activo or self.esta_bloqueado:
            return False
        acceso = nivel_de_acceso(self.rol, opcion)
        if acceso is None:
            return False
        return nivel == NIVEL_CONSULTA or acceso == NIVEL_COMPLETO

    # Solo para el sitio de administración del entorno local
    @property
    def is_staff(self):
        return self.rol == Rol.ADMINISTRADOR

    def has_perm(self, perm, obj=None):
        return self.is_active and self.rol == Rol.ADMINISTRADOR

    def has_module_perms(self, app_label):
        return self.is_active and self.rol == Rol.ADMINISTRADOR


# --- Tabla 3.57 · BITACORA_AUDITORIA ------------------------------------------
class BitacoraAuditoria(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="id_usuario", related_name="registros_bitacora"
    )
    accion = models.CharField(max_length=20, choices=AccionBitacora.choices)
    entidad = models.CharField(max_length=40)
    id_registro = models.IntegerField()
    fecha_hora = models.DateTimeField(default=timezone.now)
    valores_previos = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "bitacora_auditoria"
        managed = False  # la tabla la crea bd/01_tablas.sql (D-10)

    def __str__(self):
        return f"{self.fecha_hora:%Y-%m-%d %H:%M} {self.accion} {self.entidad}#{self.id_registro}"
