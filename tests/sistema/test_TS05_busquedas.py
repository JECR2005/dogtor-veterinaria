"""TS-05 · Tiempo de búsqueda (Tabla 4.15, RNF-05): con más de 1,000 mascotas, respuesta en 2 s o menos.

En la integración continua se mide en el servidor (vista, consulta y plantilla) con 1,050 mascotas y 30 días
de historial. En la laptop se mide además de punta a punta sobre https con `tests/carga/ts05_busquedas.py`
(docs/gestion/carga/ts05_resultado.md).
"""

import time

import pytest
from django.core.management import call_command

from catalogos.models import Mascota
from seguridad.models import Rol

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

LIMITE_SEGUNDOS = 2.0
BUSQUEDAS = [
    ("Cliente por nombre", "/clientes/", {"q": "María"}),
    ("Cliente por apellido sin acento", "/clientes/", {"q": "martinez"}),
    ("Cliente por nombre y apellido", "/clientes/", {"q": "ana lopez"}),
    ("Cliente por teléfono", "/clientes/", {"q": "8330000"}),
    ("Cliente por nombre de mascota", "/clientes/", {"q": "Firulais"}),
    ("Cliente sin coincidencias", "/clientes/", {"q": "Zzyzx"}),
    ("Clientes con bajas incluidas", "/clientes/", {"q": "José", "bajas": "1"}),
    ("Producto por nombre", "/inventario/productos/", {"q": "vacuna"}),
    ("Producto por código", "/inventario/productos/", {"q": "ALI-001"}),
    ("Productos con stock bajo", "/inventario/productos/", {"alerta": "stock_bajo"}),
    ("Tickets de un día con historial", "/ventas/", {}),
]


def test_TS05_las_busquedas_responden_en_2_segundos_con_mas_de_1000_mascotas(client, crear_usuario):
    call_command("cargar_datos_prueba", mascotas=1050, historial=30)
    assert Mascota.objects.count() >= 1050
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    lentas = []
    for que, ruta, parametros in BUSQUEDAS:
        client.get(ruta, parametros)  # la primera vez compila la plantilla
        inicio = time.perf_counter()
        respuesta = client.get(ruta, parametros)
        segundos = time.perf_counter() - inicio
        assert respuesta.status_code == 200, que
        if segundos > LIMITE_SEGUNDOS:
            lentas.append(f"{que}: {segundos:.2f} s")
    assert lentas == []
