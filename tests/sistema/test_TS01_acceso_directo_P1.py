"""S1-20 · Adelanto de TS-01: acceso por dirección directa a cada pantalla de P1 con cada rol (RNF-01, RI-11).

Recorre TODAS las rutas del sistema, también las que llevan un número (ficha de cliente, cita, empleado…), y
las abre con los cuatro roles escribiendo la dirección. Lo esperado sale de la Tabla 4.9:

- Sin sesión: toda ruta protegida lleva al inicio de sesión.
- Rol sin la opción: «Acceso denegado» (403).
- Rol con la opción: la pantalla responde (200), o 405 si la ruta solo acepta POST, o 404 si el registro no le
  corresponde (D-17 y Tabla 4.9: el estilista no abre la cita, el cliente ni la mascota de un veterinario).
  Nunca 403 ni un error 500.
- Con nivel de consulta (○), enviar un formulario (POST) a cualquier ruta protegida: 403, y no cambia nada.

Si alguien agrega una pantalla nueva, esta prueba la incluye sola. Desde P2 incluye Inventario y Compras
(S2-12): solo el Administrador las abre; los otros tres roles reciben 403 y no pueden enviar nada.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone

from agenda import services as agenda
from agenda.models import Cita
from catalogos.models import CategoriaServicio, Cliente, Mascota, Puesto
from catalogos.services import abrir_expediente
from clinico.services import abrir_consulta, emitir_receta, registrar_aplicacion
from seguridad.menu import NIVEL_COMPLETO, NIVEL_CONSULTA, ROLES, nivel_de_acceso
from seguridad.models import Usuario
from seguridad.permisos import VISTAS_PUBLICAS
from tests import fabricas
from tests.fabricas import en

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]


def _rutas(patrones=None, espacio=""):
    for patron in get_resolver().url_patterns if patrones is None else patrones:
        if isinstance(patron, URLResolver):
            yield from _rutas(
                patron.url_patterns, f"{espacio}{patron.namespace}:" if patron.namespace else espacio
            )
        elif isinstance(patron, URLPattern) and patron.name:
            yield f"{espacio}{patron.name}", patron.callback, list(patron.pattern.converters)


RUTAS = [
    (nombre, vista, parametros) for nombre, vista, parametros in _rutas() if nombre not in VISTAS_PUBLICAS
]
IDS = [nombre for nombre, *_ in RUTAS]


@pytest.fixture
def datos():
    """Un registro de cada tipo para llenar los números de las direcciones."""
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    consulta = fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    mascota = fabricas.mascota()
    abrir_expediente(mascota)
    cita = agenda.agendar(mascota, laura, consulta, en("10:00"))
    cuenta = Usuario.objects.create_user("laura", "Clave-Prueba-2026", empleado=laura, rol="Veterinario")
    proveedor = fabricas.proveedor()
    producto = fabricas.producto(proveedor=proveedor)
    pedido = fabricas.pedido(proveedor, laura, [(producto, 5, "100")])
    # La consulta va en otra cita: la de «id_cita» queda sin abrir para probar «Atender»
    con_consulta = agenda.agendar(mascota, laura, consulta, en("11:00"))
    abierta = abrir_consulta(con_consulta, laura, {"sintomas": "Revisión", "peso_kg": Decimal("10")})
    vacuna = fabricas.producto("VAC-TS", "Vacuna", stock_minimo=0)
    fabricas.lote(vacuna, 5, 100)
    (aplicada,) = registrar_aplicacion(
        abierta, laura, vacuna, 1, "1 mL", timezone.localdate() + timedelta(days=365)
    )
    receta = emitir_receta(abierta, laura, [(vacuna, "1", "Única", 1, None)])
    return {
        "id_aplicacion": aplicada.pk,
        "id_receta": receta.pk,
        "id_consulta": abierta.pk,
        "id_pedido": pedido.pk,
        "id_producto": producto.pk,
        "id_proveedor": proveedor.pk,
        "id_cliente": mascota.cliente_id,
        "id_mascota": mascota.pk,
        "id_cita": cita.pk,
        "id_empleado": laura.pk,
        "id_servicio": consulta.pk,
        "id_usuario": cuenta.pk,
    }


def _url(nombre, parametros, datos):
    return reverse(nombre, kwargs={p: datos[p] for p in parametros})


def _usuario(crear_usuario, rol):
    return crear_usuario(f"ts01_{rol.lower()}", rol=rol)


def test_TS01_todas_las_rutas_protegidas_declaran_su_permiso():
    assert [nombre for nombre, vista, _ in RUTAS if not hasattr(vista, "dogtor_permiso")] == []


@pytest.mark.parametrize("nombre, vista, parametros", RUTAS, ids=IDS)
def test_TS01_sin_sesion_ninguna_pantalla_abre(client, datos, nombre, vista, parametros):
    respuesta = client.get(_url(nombre, parametros, datos))
    assert respuesta.status_code == 302 and respuesta.url.startswith("/cuenta/entrar/")


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("nombre, vista, parametros", RUTAS, ids=IDS)
def test_TS01_cada_rol_por_direccion_directa(client, crear_usuario, datos, rol, nombre, vista, parametros):
    usuario = _usuario(crear_usuario, rol)
    client.force_login(usuario)
    opcion, nivel = vista.dogtor_permiso
    respuesta = client.get(_url(nombre, parametros, datos), {"start": "2026-01-01", "end": "2026-01-08"})
    if usuario.tiene_permiso(opcion, nivel or NIVEL_CONSULTA):
        assert respuesta.status_code in (200, 405, 404), f"{rol} en {nombre}: {respuesta.status_code}"
        if respuesta.status_code == 404:  # D-17 y Tabla 4.9: el estilista no abre lo de un veterinario
            assert (nombre, rol) in {
                ("clinico:atender", "Veterinario"),  # solo el veterinario asignado atiende la cita
                ("clinico:receta", "Veterinario"),  # y solo él emite la receta de su consulta
                ("agenda:cita", "Estilista"),
                ("catalogos:ficha", "Estilista"),
                ("catalogos:mascota", "Estilista"),
            }
    else:
        assert respuesta.status_code == 403, f"{rol} en {nombre}: {respuesta.status_code}"
        assert "Acceso denegado" in respuesta.content.decode()


# Solo los roles SIN nivel completo en la opción de la ruta (los demás se prueban en cada pantalla)
SIN_NIVEL_COMPLETO = [
    (rol, nombre, vista, parametros)
    for nombre, vista, parametros in RUTAS
    for rol in ROLES
    if nivel_de_acceso(rol, vista.dogtor_permiso[0]) != NIVEL_COMPLETO
]


@pytest.mark.parametrize(
    "rol, nombre, vista, parametros", SIN_NIVEL_COMPLETO, ids=[f"{r}-{n}" for r, n, *_ in SIN_NIVEL_COMPLETO]
)
def test_TS01_sin_nivel_completo_no_se_modifica_nada(
    client, crear_usuario, datos, rol, nombre, vista, parametros
):
    client.force_login(_usuario(crear_usuario, rol))
    antes = (
        Cliente.objects.filter(activo=True).count(),
        Mascota.objects.count(),
        list(Cita.objects.values()),
    )
    respuesta = client.post(_url(nombre, parametros, datos), {"motivo": "intento", "nombre": "X"})
    assert respuesta.status_code == 403, f"{rol} envió a {nombre}: {respuesta.status_code}"
    assert (
        Cliente.objects.filter(activo=True).count(),
        Mascota.objects.count(),
        list(Cita.objects.values()),
    ) == antes


def test_TS01_el_estilista_no_abre_la_cita_de_un_veterinario_por_ninguna_ruta(client, crear_usuario, datos):
    """D-17 y Tabla 4.9: ni por el detalle (404) ni por reprogramar (403)."""
    client.force_login(_usuario(crear_usuario, "Estilista"))
    assert client.get(f"/agenda/citas/{datos['id_cita']}/").status_code == 404
    assert client.get(f"/agenda/citas/{datos['id_cita']}/reprogramar/").status_code == 403
