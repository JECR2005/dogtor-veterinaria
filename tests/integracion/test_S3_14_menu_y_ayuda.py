"""S3-14 · Interfaz y seguridad de P3: ningún rol ve más de lo suyo (RNF-01, RNF-02, RNF-07).

- El menú de cada rol lleva solo a sus opciones; las de otros roles no aparecen ni como enlace.
- Contadores de pendientes junto a Recordatorios, Inventario y Estética (apartado 4.4).
- En la tableta el menú del estilista se reduce a Inicio, Agenda, Estética y Mi cuenta.
- La Ayuda de los cuatro roles explica los procedimientos de P3.
"""

import pytest
from django.urls import reverse

from catalogos.models import CategoriaServicio, Puesto
from clinico.services import registrar_estetica
from seguridad.menu import OPCIONES, RUTAS
from seguridad.models import Rol, Usuario
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

ROLES = [Rol.ADMINISTRADOR, Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA]


@pytest.mark.parametrize("rol", ROLES)
def test_S3_14_el_menu_lleva_solo_a_las_opciones_del_rol(client, crear_usuario, rol):
    client.force_login(crear_usuario("usuario", rol=rol))
    inicio = client.get("/").content.decode()
    menu = inicio[
        inicio.index('aria-label="Menú principal"') : inicio.index("</nav>", inicio.index("Menú principal"))
    ]
    for clave, etiqueta, _icono, _submenu, accesos in OPCIONES:
        ruta = RUTAS.get(clave)
        if not ruta:
            continue  # opción de un prototipo posterior (Ventas en P4, Bitácora en P5)
        direccion = reverse(ruta)
        if rol in accesos:
            assert f'href="{direccion}"' in menu, f"{rol} no ve {etiqueta}"
        else:
            assert etiqueta not in menu, f"{rol} ve {etiqueta}"
            if clave not in ("inicio", "clientes"):
                assert f'href="{direccion}' not in inicio, f"{rol} tiene un enlace a {etiqueta}"


def test_S3_14_contadores_de_pendientes_en_el_menu(client, crear_usuario):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    mario = fabricas.empleado(Puesto.ESTILISTA, nombre="Mario")
    fabricas.cuenta(mario, "mario", rol=Rol.ESTILISTA)
    bano = fabricas.servicio("Baño", CategoriaServicio.ESTETICA, 60)
    canela = fabricas.paciente("Canela")
    fabricas.cita_de_hoy(canela, mario, bano, "12:00")
    atendida = fabricas.cita_de_hoy(fabricas.paciente("Toby"), mario, bano, "10:00")
    datos = {"estado_pelaje_piel": "Opaco", "hallazgos": "Garrapatas", "aviso_veterinario": True}
    registrar_estetica(atendida, mario, datos)
    vacuna = fabricas.producto("VAC-002", "Vacuna antirrábica", stock_minimo=0)
    fabricas.aplicacion(canela, laura, vacuna, 2)

    client.force_login(Usuario.objects.get(nombre_usuario="mario"))
    assert 'data-contador="estetica">1<' in client.get("/").content.decode()  # el baño de Canela

    client.force_login(crear_usuario("vet", rol=Rol.VETERINARIO))
    assert 'data-contador="estetica">1<' in client.get("/").content.decode()  # el aviso de Toby

    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert 'data-contador="recordatorios">1<' in client.get("/").content.decode()  # la dosis de Canela

    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    fabricas.lote(fabricas.producto("MED-001", "Antibiótico", stock_minimo=0), 5, dias_para_caducar=10)
    inicio = client.get("/").content.decode()
    assert 'data-contador="recordatorios">1<' in inicio and 'data-contador="estetica">1<' in inicio
    assert 'data-contador="inventario">1<' in inicio  # el lote que caduca en 10 días


def test_S3_14_sin_pendientes_no_hay_contador(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    assert "data-contador=" not in client.get("/").content.decode()


def test_S3_14_en_la_tableta_el_estilista_no_ve_clientes(client, crear_usuario):
    client.force_login(crear_usuario("estilista", rol=Rol.ESTILISTA))
    inicio = client.get("/").content.decode()
    clientes = inicio.index('href="/clientes/" title="Clientes y mascotas"')
    assert 'class="nav-item d-none d-xl-block"' in inicio[clientes - 200 : clientes]
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert "d-none d-xl-block" not in client.get("/").content.decode()


@pytest.mark.parametrize(
    "rol, textos",
    [
        (Rol.RECEPCIONISTA, ["Contactar a los clientes del día", "Contactado y agendar"]),
        (
            Rol.VETERINARIO,
            [
                "Atender una consulta",
                "Aplicar una vacuna",
                "Emitir una receta",
                "Firmar la consulta",
                "Avisos de estética",
                "Antes de firmar capture",
            ],
        ),
        (
            Rol.ESTILISTA,
            ["Registrar la atención de estética", "Avisar al veterinario", "describa el hallazgo"],
        ),
        (Rol.ADMINISTRADOR, ["Consultar sin modificar", "Consulta clínica", "Recordatorios"]),
    ],
)
def test_S3_14_la_ayuda_de_cada_rol_explica_P3(client, crear_usuario, rol, textos):
    client.force_login(crear_usuario("usuario", rol=rol))
    ayuda = client.get("/ayuda/").content.decode()
    for texto in textos:
        assert texto in ayuda, texto
    assert "prototipo P3" not in ayuda  # ya no hay procedimientos «por venir» de P3


def test_S3_14_la_ayuda_no_explica_lo_de_otros_roles(client, crear_usuario):
    client.force_login(crear_usuario("estilista", rol=Rol.ESTILISTA))
    ayuda = client.get("/ayuda/").content.decode()
    assert "Firmar la consulta" not in ayuda and "Contactar a los clientes" not in ayuda
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    ayuda = client.get("/ayuda/").content.decode()
    assert "Registrar la atención de estética" not in ayuda and "Emitir una receta" not in ayuda
