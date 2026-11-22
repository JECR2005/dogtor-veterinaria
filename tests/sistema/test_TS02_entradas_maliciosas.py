"""TS-02 · Validación de entradas (Tabla 4.15, RNF-01): texto malicioso en formularios y buscadores.

Criterio: ninguna entrada altera la base de datos ni se ejecuta en la página. Se complementa con el escaneo de
OWASP ZAP sobre el entorno con https (D-22; `docker compose run --rm zap`, docs/gestion/zap/).

- Scripts (XSS): lo que se guarda se muestra escapado (`&lt;script&gt;`), nunca como etiqueta.
- Inyección SQL: los buscadores y filtros de TODAS las pantallas reciben comillas y sentencias; ninguna
  responde con error 500, ninguna encuentra registros que no coinciden y la base queda igual.
- Revisión del código: no hay `|safe`, `mark_safe`, `autoescape off`, `.raw()` ni `.extra()`, y las
  consultas con cursor solo usan texto fijo o parámetros.
"""

import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.db import connection
from django.urls import reverse

from catalogos.models import CategoriaServicio, Cliente, Mascota, PreferenciaContacto, Proveedor, Puesto, Sexo
from clinico import services as clinico
from clinico.models import Consulta
from seguridad.models import Rol, Usuario
from seguridad.permisos import VISTAS_PUBLICAS
from tests import fabricas
from tests.sistema.test_TS01_acceso_directo import _rutas

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

SCRIPT = '<script>alert("dogtor")</script>'
IMAGEN = "<img src=x onerror=alert(1)>"
INYECCIONES = [
    "' OR '1'='1",
    "'; DROP TABLE dbo.cliente; --",
    "1; DELETE FROM dbo.usuario --",
    "%' UNION SELECT nombre_usuario, hash_contrasena FROM dbo.usuario --",
    "]; EXEC xp_cmdshell 'dir' --",
]
PARAMETROS = [
    "q", "estado", "categoria", "alerta", "fecha", "empleado", "servicio", "proveedor", "pagina", "start",
    "end", "desde", "hasta", "usuario", "accion", "entidad", "pendientes", "inactivos", "bajas", "canceladas",
]  # fmt: skip
RAIZ = Path(__file__).resolve().parents[2]


def _no_se_ejecuta(html, *cargas):
    for carga in cargas:
        assert carga not in html, f"La página muestra sin escapar: {carga}"


def _estado_de_la_base():
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tablas = cursor.fetchone()[0]
    return tablas, Cliente.objects.count(), Usuario.objects.count(), Mascota.objects.count()


# --- Scripts guardados en formularios ------------------------------------------------------------
def test_TS02_un_script_en_cliente_y_mascota_se_guarda_tal_cual_y_se_muestra_escapado(client, crear_usuario):
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    cliente = {
        "nombre": "Lucía",
        "apellido_paterno": "Pruebas",
        "apellido_materno": "",
        "telefono": "8335550199",
        "correo": "",
        "direccion": SCRIPT,
        "preferencia_contacto": PreferenciaContacto.TELEFONO,
        "rfc": "",
        "razon_social_fiscal": "",
        "regimen_fiscal": "",
        "cp_fiscal": "",
        "acepto_aviso_privacidad": "on",
    }
    client.post("/clientes/nuevo/", cliente)
    lucia = Cliente.objects.get(apellido_paterno="Pruebas")
    assert lucia.direccion == SCRIPT  # se guarda como texto, sin alterar la base
    ficha = client.get(f"/clientes/{lucia.pk}/").content.decode()
    _no_se_ejecuta(ficha, SCRIPT)
    assert "&lt;script&gt;alert(&quot;dogtor&quot;)&lt;/script&gt;" in ficha

    raza = fabricas.mascota().raza
    mascota = {
        "nombre": "Michi",
        "raza": raza.pk,
        "sexo": Sexo.HEMBRA,
        "fecha_nacimiento": "2022-03-15",
        "peso_actual": "4.20",
        "color": IMAGEN,
        "alergias": SCRIPT,
        "antecedentes": "",
    }
    client.post(f"/clientes/{lucia.pk}/mascotas/nueva/", mascota)
    michi = Mascota.objects.get(nombre="Michi")
    assert michi.color == IMAGEN
    for url in (f"/clientes/mascotas/{michi.pk}/", f"/clientes/{lucia.pk}/", "/clientes/?q=Pruebas"):
        _no_se_ejecuta(client.get(url).content.decode(), SCRIPT, IMAGEN)


def test_TS02_un_script_en_proveedor_y_en_la_consulta_no_se_ejecuta(client, crear_usuario):
    client.force_login(crear_usuario("admin", rol=Rol.ADMINISTRADOR))
    client.post(
        "/compras/proveedores/nuevo/",
        {
            "razon_social": "Distribuidora XSS (ficticia)",
            "rfc": "",
            "contacto": IMAGEN,
            "telefono": "8331234567",
            "correo": "",
            "condiciones_pago": SCRIPT,
        },
    )
    proveedor = Proveedor.objects.get(razon_social__startswith="Distribuidora XSS")
    assert proveedor.condiciones_pago == SCRIPT
    for url in ("/compras/proveedores/", f"/compras/proveedores/{proveedor.pk}/editar/"):
        _no_se_ejecuta(client.get(url).content.decode(), SCRIPT, IMAGEN)

    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    max_ = fabricas.paciente("Max", alergias=SCRIPT)
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    consulta = clinico.abrir_consulta(cita, laura, {"sintomas": SCRIPT, "peso_kg": Decimal("10")})
    client.force_login(fabricas.cuenta(laura, "laura"))
    for url in (f"/clinica/consultas/{consulta.pk}/", f"/clinica/mascotas/{max_.pk}/historial/", "/clinica/"):
        _no_se_ejecuta(client.get(url).content.decode(), SCRIPT)
    assert Consulta.objects.get(pk=consulta.pk).sintomas == SCRIPT


# --- Inyección SQL en buscadores y filtros de todas las pantallas --------------------------------
RUTAS_SIN_NUMERO = sorted(
    nombre for nombre, vista, parametros in _rutas() if not parametros and nombre not in VISTAS_PUBLICAS
)


@pytest.mark.parametrize("rol", [Rol.ADMINISTRADOR, Rol.RECEPCIONISTA, Rol.VETERINARIO])
def test_TS02_ninguna_pantalla_falla_ni_cambia_la_base_con_inyeccion_sql(client, crear_usuario, rol):
    fabricas.mascota("Firulais", "Ana")
    client.force_login(crear_usuario("usuario", rol=rol))
    antes = _estado_de_la_base()
    for carga in INYECCIONES:
        for nombre in RUTAS_SIN_NUMERO:
            respuesta = client.get(reverse(nombre), {p: carga for p in PARAMETROS})
            assert respuesta.status_code < 500, f"{nombre} con «{carga}»: {respuesta.status_code}"
    assert _estado_de_la_base() == antes


def test_TS02_la_busqueda_trata_la_inyeccion_como_texto(client, crear_usuario):
    ana = fabricas.mascota("Firulais", "Ana").cliente
    fila = f'href="/clientes/{ana.pk}/"'  # el renglón de Ana en los resultados
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert fila in client.get("/clientes/", {"q": "Ana"}).content.decode()
    for carga in INYECCIONES:
        pagina = client.get("/clientes/", {"q": carga}).content.decode()
        assert fila not in pagina, f"«{carga}» encontró clientes que no coinciden"


def test_TS02_el_inicio_de_sesion_no_se_salta_con_inyeccion(client, crear_usuario):
    crear_usuario("administrador", rol=Rol.ADMINISTRADOR)
    for usuario, contrasena in [
        ("administrador' --", "x"),
        ("administrador", "' OR '1'='1"),
        ("' OR 1=1 --", "' OR 1=1 --"),
    ]:
        respuesta = client.post("/cuenta/entrar/", {"nombre_usuario": usuario, "contrasena": contrasena})
        assert respuesta.status_code == 200
        assert "_auth_user_id" not in client.session


# --- Revisión del código ------------------------------------------------------------------------------
CARPETAS = [
    "agenda",
    "catalogos",
    "clinico",
    "config",
    "inventario",
    "recordatorios",
    "reportes",
    "seguridad",
    "ventas",
]
# Consultas con cursor revisadas a mano: texto fijo o parámetros, nunca datos del usuario en el SQL
CURSOR_REVISADO = {
    "config/views.py",  # SELECT 1 de /salud/
    "clinico/services.py",  # sp_set_session_context con 1 o NULL fijos (S5-07)
}


def _archivos(extension):
    for carpeta in CARPETAS + (["templates"] if extension == ".html" else []):
        yield from (p for p in (RAIZ / carpeta).rglob(f"*{extension}") if "migrations" not in p.parts)


def test_TS02_las_plantillas_no_desactivan_el_escape():
    peligrosos = re.compile(r"\|\s*safe\b|autoescape\s+off|mark_safe|format_html_join")
    encontrados = [
        str(p.relative_to(RAIZ))
        for p in _archivos(".html")
        if peligrosos.search(p.read_text(encoding="utf-8"))
    ]
    assert encontrados == []


def test_TS02_el_codigo_no_arma_sql_con_datos_del_usuario():
    sospechosos = []
    for archivo in _archivos(".py"):
        texto = archivo.read_text(encoding="utf-8")
        relativo = archivo.relative_to(RAIZ).as_posix()
        if re.search(r"\.raw\(|\.extra\(|RawSQL\(|mark_safe\(", texto):
            sospechosos.append(relativo)
        if "cursor.execute(" in texto and relativo not in CURSOR_REVISADO:
            sospechosos.append(relativo)
    assert sospechosos == []
