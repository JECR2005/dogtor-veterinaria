"""Servicios (reglas de negocio) del componente «Catálogos».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P1 y P2:

- RF-01: alta, edición y baja lógica de clientes con aviso de privacidad (P1).
- RF-02 y RD-10: alta de mascota que abre su único expediente clínico (P1).
- RF-03 y RD-01: empleados con horario; cédula obligatoria para el veterinario (P1).
- RF-04: catálogo de servicios con precio y duración (P1).
"""

from functools import reduce
from operator import and_

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import CharField, Count, Func, Q

from seguridad import bitacora
from seguridad.menu import NIVEL_COMPLETO
from seguridad.models import AccionBitacora, Rol, Usuario

from .forms import solo_digitos
from .models import Cliente, Empleado, HorarioLaboral


class OperacionNoValida(Exception):
    """Regla de negocio incumplida; el mensaje se muestra tal cual al usuario (RI-08)."""


def dar_de_baja_cliente(cliente, usuario):
    """Baja lógica de un cliente (RF-01, RNF-08) con su registro en la bitácora (RNF-03, S1-07).

    El cliente no se borra: queda con activo = 0 y deja de aparecer en búsquedas; su historial y sus
    tickets se conservan. Solo un rol con Clientes en nivel completo (Recepcionista) puede hacerlo.
    """
    if not usuario.tiene_permiso("clientes", NIVEL_COMPLETO):
        raise PermissionDenied
    with transaction.atomic():
        actual = Cliente.objects.select_for_update().get(pk=cliente.pk)
        if not actual.activo:
            raise OperacionNoValida("El cliente ya está dado de baja.")
        previos = bitacora.valores_de(actual)
        Cliente.objects.filter(pk=actual.pk).update(activo=False)
        bitacora.registrar(usuario, AccionBitacora.BAJA_LOGICA, actual, previos)
    cliente.activo = False
    return cliente


class SinAcentos(Func):
    """Compara sin acentos ni mayúsculas. Collate() de Django pone la intercalación entre corchetes,
    que SQL Server no acepta en COLLATE; por eso se escribe fija aquí."""

    template = "%(expressions)s COLLATE Modern_Spanish_CI_AI"
    output_field = CharField()


def buscar_clientes(texto="", incluir_dados_de_baja=False):
    """Búsqueda de UI-05 y de la barra superior: por nombre, apellidos, teléfono o nombre de mascota.

    Cada palabra escrita debe aparecer en alguno de esos datos («ana 833» encuentra a Ana con teléfono
    que contiene 833). Los clientes dados de baja no aparecen (RF-01), salvo que el Administrador pida
    verlos para consultar su historial.
    """
    clientes = Cliente.objects.all()
    if not incluir_dados_de_baja:
        clientes = clientes.filter(activo=True)
    condiciones = []
    for palabra in (texto or "").split():
        condicion = (
            Q(_nombre__icontains=palabra)
            | Q(_paterno__icontains=palabra)
            | Q(_materno__icontains=palabra)
            | Q(_mascota__icontains=palabra)
        )
        digitos = solo_digitos(palabra)
        if len(digitos) >= 3:
            condicion |= Q(telefono__contains=digitos)
        condiciones.append(condicion)
    if condiciones:
        # Sin distinguir acentos ni mayúsculas: «martinez» encuentra a «Martínez» (RI-13, RNF-07)
        ids = (
            clientes.annotate(
                _nombre=SinAcentos("nombre"),
                _paterno=SinAcentos("apellido_paterno"),
                _materno=SinAcentos("apellido_materno"),
                _mascota=SinAcentos("mascotas__nombre"),
            )
            .filter(reduce(and_, condiciones))
            .values("pk")
        )
        clientes = Cliente.objects.filter(pk__in=ids)
    return clientes.annotate(total_mascotas=Count("mascotas")).order_by(
        "apellido_paterno", "apellido_materno", "nombre", "pk"
    )


def registrar_cliente(formulario):
    """Alta de cliente (RF-01). El formulario ya exige el aviso de privacidad; la base lo vuelve a exigir."""
    with transaction.atomic():
        return formulario.save()


MENSAJE_EXPEDIENTE_DUPLICADO = "La mascota ya tiene expediente; no se puede abrir un segundo (RD-10)."


def abrir_expediente(mascota, alergias=None, antecedentes=None):
    """RD-10: una mascota tiene un solo expediente. La base lo garantiza con UQ_expediente_mascota."""
    from clinico.models import ExpedienteClinico

    if ExpedienteClinico.objects.filter(mascota=mascota).exists():
        raise OperacionNoValida(MENSAJE_EXPEDIENTE_DUPLICADO)
    return ExpedienteClinico.objects.create(mascota=mascota, alergias=alergias, antecedentes=antecedentes)


def registrar_mascota(cliente, formulario):
    """Alta de mascota (RF-02) y apertura de su expediente en la MISMA transacción (RD-10, TI-01).

    Si el expediente no se puede crear, la mascota tampoco queda guardada.
    """
    if not cliente.activo:
        raise OperacionNoValida("El cliente está dado de baja; no se le pueden registrar mascotas.")
    with transaction.atomic():
        mascota = formulario.save(commit=False)
        mascota.cliente = cliente
        mascota.save()
        abrir_expediente(mascota, **formulario.datos_expediente())
    return mascota


# --- UI-03 · Empleados y usuarios (S1-10, RF-03, RD-01) ----------------------
def _guardar_horario(empleado, jornadas):
    """Reemplaza el horario semanal del empleado por las jornadas [(día, entrada, salida)]."""
    HorarioLaboral.objects.filter(empleado=empleado).delete()
    HorarioLaboral.objects.bulk_create(
        HorarioLaboral(empleado=empleado, dia_semana=dia, hora_entrada=entrada, hora_salida=salida)
        for dia, entrada, salida in jornadas
    )


def guardar_empleado(form_empleado, form_horario, form_cuenta, administrador):
    """Alta o edición de un empleado con su horario y su cuenta, todo en una transacción (RF-03).

    - La cédula del veterinario la exigen el formulario, Empleado.clean() y la base (RD-01).
    - Un empleado inactivo no puede entrar al sistema: su cuenta se desactiva con él.
    - El Administrador no puede quitarse su propio acceso ni su rol.
    """
    if administrador.rol != Rol.ADMINISTRADOR:
        raise PermissionDenied
    with transaction.atomic():
        empleado = form_empleado.save()
        _guardar_horario(empleado, form_horario.jornadas)

        cuenta = form_cuenta.cuenta
        datos = form_cuenta.cleaned_data
        if cuenta is None and datos.get("crear"):
            Usuario.objects.create_user(
                datos["nombre_usuario"], datos["contrasena"], empleado=empleado, rol=datos["rol"]
            )
        elif cuenta is not None:
            propia = cuenta.pk == administrador.pk
            campos = []
            if not propia:
                cuenta.rol = datos["rol"]
                cuenta.activo = bool(datos.get("activa")) and empleado.activo
                campos += ["rol", "activo"]
            if datos.get("contrasena"):
                cuenta.set_password(datos["contrasena"])
                campos.append("password")
            if campos:
                cuenta.save(update_fields=campos)
        if not empleado.activo:
            if cuenta is not None and cuenta.pk == administrador.pk:
                raise OperacionNoValida("No puede desactivar su propio empleado.")
            Usuario.objects.filter(empleado=empleado).update(activo=False)
    return empleado


def empleados_con_cuenta():
    return (
        Empleado.objects.select_related("usuario")
        .prefetch_related("horarios")
        .order_by("-activo", "puesto", "apellidos", "nombre")
    )


# --- Tabla 4.9 · El Estilista ve solo la mascota de su cita (DEF-002) ----------------------------
def solo_mascotas_de_sus_citas(usuario):
    """Tabla 4.9: «Clientes y mascotas — Estilista: ○ solo la mascota de su cita»."""
    return usuario.rol == Rol.ESTILISTA


def mascotas_visibles(usuario, mascotas=None):
    """Mascotas que el usuario puede consultar. El Estilista, solo las que tienen una cita con él."""
    from .models import Mascota

    mascotas = Mascota.objects.all() if mascotas is None else mascotas
    if solo_mascotas_de_sus_citas(usuario):
        mascotas = mascotas.filter(citas__empleado_id=usuario.empleado_id).distinct()
    return mascotas


def clientes_visibles(usuario, clientes):
    """Clientes que el usuario puede consultar. El Estilista, solo los dueños de las mascotas de sus citas."""
    if solo_mascotas_de_sus_citas(usuario):
        clientes = clientes.filter(pk__in=mascotas_visibles(usuario).values("cliente_id"))
    return clientes
