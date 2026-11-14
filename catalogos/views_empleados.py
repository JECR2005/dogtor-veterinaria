"""UI-03 · Empleados y usuarios (S1-10, RF-03, RD-01). Solo el Administrador (Tabla 4.9: Administración ●).

Puesto, horario semanal, cédula obligatoria para el veterinario y cuenta de acceso con rol.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from seguridad.menu import NIVEL_COMPLETO
from seguridad.permisos import requiere_permiso

from . import services
from .forms import CuentaForm, EmpleadoForm, HorarioSemanalForm
from .models import Empleado


def _horario_inicial(empleado):
    if empleado is None:  # sugerencia para un empleado nuevo: lunes a sábado de 9:00 a 19:00
        return {
            f"{parte}_{dia}": hora
            for dia in range(1, 7)
            for parte, hora in (("entrada", "09:00"), ("salida", "19:00"))
        }
    inicial = {}
    for horario in empleado.horarios.all():
        inicial[f"entrada_{horario.dia_semana}"] = horario.hora_entrada
        inicial[f"salida_{horario.dia_semana}"] = horario.hora_salida
    return inicial


def _cuenta_de(empleado):
    return getattr(empleado, "usuario", None) if empleado is not None else None


def _formulario(request, empleado=None):
    datos = request.POST if request.method == "POST" else None
    cuenta = _cuenta_de(empleado)
    form_empleado = EmpleadoForm(datos, instance=empleado, prefix="empleado")
    if cuenta is not None and cuenta.pk == request.user.pk and "activo" in form_empleado.fields:
        form_empleado.fields["activo"].disabled = True  # nadie se quita su propio acceso
    puesto = request.POST.get("empleado-puesto") if datos else getattr(empleado, "puesto", None)
    form_horario = HorarioSemanalForm(
        datos, initial=_horario_inicial(empleado), prefix="horario", puesto=puesto
    )
    form_cuenta = CuentaForm(datos, cuenta=cuenta, administrador=request.user, prefix="cuenta")

    if request.method == "POST":
        validos = [f.is_valid() for f in (form_empleado, form_horario, form_cuenta)]
        if all(validos):
            try:
                guardado = services.guardar_empleado(form_empleado, form_horario, form_cuenta, request.user)
            except services.OperacionNoValida as error:
                messages.error(request, str(error))
            else:
                accion = "actualizado" if empleado else "registrado"
                messages.success(request, f"Empleado «{guardado.nombre_completo}» {accion}.")
                return redirect("empleados:lista")

    contexto = {
        "empleado": empleado,
        "form_empleado": form_empleado,
        "form_horario": form_horario,
        "form_cuenta": form_cuenta,
        "hay_errores": any(f.errors for f in (form_empleado, form_horario, form_cuenta)),
    }
    return render(request, "catalogos/empleados/formulario.html", contexto)


@requiere_permiso("administracion", NIVEL_COMPLETO)
def lista(request):
    """UI-03 · Lista de empleados con puesto, cédula, horario y cuenta."""
    return render(request, "catalogos/empleados/lista.html", {"empleados": services.empleados_con_cuenta()})


@requiere_permiso("administracion", NIVEL_COMPLETO)
def nuevo(request):
    return _formulario(request)


@requiere_permiso("administracion", NIVEL_COMPLETO)
def editar(request, id_empleado):
    empleado = get_object_or_404(Empleado.objects.select_related("usuario"), pk=id_empleado)
    return _formulario(request, empleado)
