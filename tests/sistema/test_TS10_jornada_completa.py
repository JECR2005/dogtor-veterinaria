"""S5-17 · TS-10 (Tabla 4.15): una jornada completa de la clínica, de la apertura al respaldo.

Recorre por las pantallas, en orden, lo que pasa en un día con los datos ficticios de `cargar_datos_prueba`
y los cuatro roles, como lo harían con el navegador. Es el ensayo automático de TA-09
(docs/gestion/guion_aceptacion_P5.md):

1. Apertura: las tareas de la mañana generan los recordatorios y el PDF de la agenda (S5-08, TS-11).
2. Recepción registra a una clienta nueva con su mascota y le agenda una cita para el siguiente día hábil.
3. El Veterinario atiende a Max: vacuna, receta de amoxicilina y firma.
4. El Estilista registra el baño de Canela.
5. Recepción cobra las tres citas del día, vende un collar en mostrador y un medicamento con control solo con
   el folio de la receta (RD-12); recibe efectivo, tarjeta y transferencia y liquida el saldo de Pedro.
6. Cierre: el corte cuadra con los pagos y con lo vendido, el inventario cuadra con su kardex (RD-09), la
   bitácora tiene cada cobro (RNF-03) y el respaldo de la base queda verificado (RNF-04).

Criterio: todos los pasos terminan como dice el guion y ningún dato queda inconsistente al cierre.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.models import Sum
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import Cliente, Mascota, PreferenciaContacto, Producto, Raza, Servicio, Sexo
from clinico.models import Consulta
from inventario.models import Lote
from scripts import respaldo
from seguridad.models import BitacoraAuditoria, Usuario
from ventas import services as ventas
from ventas.models import EstadoVenta, Venta

pytestmark = [pytest.mark.sistema, pytest.mark.django_db]

HOY = timezone.localdate()
FOLIO = f"T-{HOY:%Y}-"


@pytest.fixture
def datos():
    """Lo que el observador prepara antes de la jornada: datos ficticios limpios."""
    call_command("cargar_datos_prueba", mascotas=0)


def _entrar(client, cuenta):
    client.force_login(Usuario.objects.get(nombre_usuario=cuenta))


def _texto(respuesta):
    return respuesta.content.decode()


def _siguiente_dia_habil():
    dia = HOY + timedelta(days=1)
    return dia + timedelta(days=1) if dia.isoweekday() == 7 else dia  # el domingo no hay servicio


def _receta(producto):
    datos = {
        "indicaciones_generales": "Reposo y revisión en 7 días",
        "medicamentos-TOTAL_FORMS": "4",
        "medicamentos-INITIAL_FORMS": "0",
        "medicamentos-MIN_NUM_FORMS": "4",
        "medicamentos-MAX_NUM_FORMS": "12",
    }
    for i in range(4):
        fila = (producto.pk, "1 tableta", "Cada 12 horas", 7) if i == 0 else ("", "", "", "")
        for campo, valor in zip(("producto", "dosis", "frecuencia", "duracion_dias"), fila, strict=True):
            datos[f"medicamentos-{i}-{campo}"] = valor
        datos[f"medicamentos-{i}-indicaciones"] = ""
    return datos


def _lineas(*articulos, iniciales=0):
    """Formulario de líneas del ticket: (clave s-/p-, cantidad[, folio de receta])."""
    datos = {
        "lineas-TOTAL_FORMS": "6",
        "lineas-INITIAL_FORMS": str(iniciales),
        "lineas-MIN_NUM_FORMS": "6",
        "lineas-MAX_NUM_FORMS": "20",
    }
    for i, (articulo, cantidad, *folio) in enumerate(articulos):
        datos[f"lineas-{i}-articulo"] = articulo
        datos[f"lineas-{i}-cantidad"] = str(cantidad)
        datos[f"lineas-{i}-folio_receta"] = folio[0] if folio else ""
    return datos


def _cobrar_cita(client, cita, lineas, total):
    respuesta = client.post(f"/ventas/nuevo/?cita={cita.pk}", lineas, follow=True)
    contenido = _texto(respuesta)
    assert f"generado por ${total}. Registre el pago." in contenido, contenido[:2000]
    return Venta.objects.get(cita=cita)


def _pagar(client, venta, datos):
    return _texto(client.post(f"/ventas/tickets/{venta.pk}/pagar/", datos, follow=True))


def _neto(pantalla, metodo):
    inicio = pantalla.index(f'data-metodo="{metodo}"')
    celda = pantalla.index("data-neto>", inicio) + len("data-neto>")
    return pantalla[celda : pantalla.index("<", celda)]


def _respaldar_base_de_pruebas():
    """BACKUP de la base de pruebas con CHECKSUM y RESTORE VERIFYONLY, como la tarea de las 22:00 (S5-08).

    Se usa la carpeta de respaldos de la propia instancia (en la CI, SQL Server corre en un contenedor) y un
    nombre fijo que cada ejecución sobrescribe. COPY_ONLY no altera la cadena de respaldos de la instancia.
    """
    respaldo.cargar_env()
    base = connection.settings_dict["NAME"]
    assert base.startswith("test_")  # nunca sobre la base real
    with respaldo.conectar() as conexion:
        ((carpeta,),) = respaldo.ejecutar(
            conexion, "SELECT CAST(SERVERPROPERTY('InstanceDefaultBackupPath') AS NVARCHAR(400))"
        )
        separador = "\\" if "\\" in carpeta else "/"
        archivo = f"{carpeta.rstrip(separador)}{separador}{base}_TS10.bak"
        respaldo.ejecutar(
            conexion,
            f"BACKUP DATABASE {respaldo.corchetes(base)} TO DISK = ? "
            "WITH INIT, CHECKSUM, COPY_ONLY, NAME = ?",
            archivo,
            "TS-10: respaldo al cierre de la jornada",
        )
        respaldo.ejecutar(conexion, "RESTORE VERIFYONLY FROM DISK = ? WITH CHECKSUM", archivo)
        cabecera = respaldo.ejecutar(conexion, "RESTORE HEADERONLY FROM DISK = ?", archivo)[0]
    return archivo, cabecera.DatabaseName


def test_TS10_jornada_completa_de_la_apertura_al_respaldo(client, datos, tmp_path):
    ultimo = BitacoraAuditoria.objects.order_by("-id_bitacora").values_list("id_bitacora", flat=True).first()
    manana_hay_servicio = (HOY + timedelta(days=1)).isoweekday() != 7

    # 1. Apertura: recordatorios (Michi y, si mañana hay servicio, Canela) y la agenda impresa de hoy
    salida = tmp_path / "salida.txt"
    with salida.open("w", encoding="utf-8") as archivo:
        call_command("generar_recordatorios", stdout=archivo)
        call_command("generar_agenda", salida=str(tmp_path), stdout=archivo)
    apertura = salida.read_text(encoding="utf-8")
    assert f"Recordatorios nuevos: {2 if manana_hay_servicio else 1}." in apertura
    assert f"Agenda del {HOY:%d/%m/%Y}: 3 citas en" in apertura  # Toby, Max y Canela
    assert (tmp_path / f"Agenda-{HOY:%Y-%m-%d}.pdf").read_bytes().startswith(b"%PDF")

    # 2. Recepción: clienta nueva con aviso de privacidad, su mascota y una cita para el siguiente día hábil
    _entrar(client, "recepcion")
    clienta = {
        "nombre": "Rosa",
        "apellido_paterno": "Jornada",
        "apellido_materno": "Ficticia",
        "telefono": "833 555 0110",
        "preferencia_contacto": PreferenciaContacto.WHATSAPP,
        "acepto_aviso_privacidad": "on",
    }
    assert "registrad" in _texto(client.post("/clientes/nuevo/", clienta, follow=True))
    rosa = Cliente.objects.get(nombre="Rosa", apellido_paterno="Jornada")
    nube = {
        "nombre": "Nube",
        "raza": Raza.objects.get(nombre="Labrador Retriever").pk,
        "sexo": Sexo.HEMBRA,
        "fecha_nacimiento": (HOY - timedelta(days=2 * 365)).isoformat(),
        "peso_actual": "20",
        "alergias": "",
    }
    client.post(f"/clientes/{rosa.pk}/mascotas/nueva/", nube, follow=True)
    nube = Mascota.objects.get(cliente=rosa, nombre="Nube")
    veterinaria = Usuario.objects.get(nombre_usuario="veterinario").empleado
    consulta_general = Servicio.objects.get(nombre="Consulta general")
    dia_cita = _siguiente_dia_habil()
    cita_nube = {
        "servicio": consulta_general.pk,
        "empleado": veterinaria.pk,
        "fecha": dia_cita.isoformat(),
        "hora": "16:00",
    }
    respuesta = client.post(f"/agenda/nueva/?mascota={nube.pk}", cita_nube, follow=True)
    assert "Cita agendada" in _texto(respuesta)
    assert Cita.objects.get(mascota=nube).estado == EstadoCita.PROGRAMADA

    # 3. Veterinario: Max con vacuna, receta de 14 tabletas de amoxicilina, diagnóstico y firma
    _entrar(client, "veterinario")
    max_ = Mascota.objects.get(nombre="Max", cliente__telefono="8339990001")
    cita_max = Cita.objects.get(mascota=max_, fecha_hora_inicio__date=HOY)
    datos_consulta = {"sintomas": "Revisión anual y tos leve", "peso_kg": "29.10"}
    assert "Consulta de Max abierta." in _texto(
        client.post(f"/clinica/citas/{cita_max.pk}/atender/", datos_consulta, follow=True)
    )
    consulta = Consulta.objects.get(cita=cita_max)
    url = f"/clinica/consultas/{consulta.pk}/"
    vacuna = Producto.objects.get(codigo="VAC-002")
    aplicacion = {
        "producto": vacuna.pk,
        "cantidad": "1",
        "dosis": "1 mL subcutánea",
        "proxima_fecha": (HOY + timedelta(days=365)).isoformat(),
    }
    assert "Aplicación registrada: Vacuna antirrábica" in _texto(
        client.post(f"{url}aplicar/", aplicacion, follow=True)
    )
    amoxicilina = Producto.objects.get(codigo="MED-001")
    folio_receta = f"R-{HOY:%Y}-00001"
    assert f"Receta {folio_receta} emitida." in _texto(
        client.post(f"{url}receta/", _receta(amoxicilina), follow=True)
    )
    completa = {
        **datos_consulta,
        "temperatura_c": "38.7",
        "diagnostico": "Traqueítis leve",
        "tratamiento": "Amoxicilina 7 días",
        "observaciones": "",
    }
    assert "Consulta guardada." in _texto(client.post(url, completa, follow=True))
    assert "Consulta firmada." in _texto(client.post(f"{url}firmar/", follow=True))

    # 4. Estilista: el baño de Canela
    _entrar(client, "estilista")
    canela = Mascota.objects.get(nombre="Canela", cliente__telefono="8339990004")
    cita_canela = Cita.objects.get(mascota=canela, fecha_hora_inicio__date=HOY)
    registro = {
        "estado_pelaje_piel": "Pelaje sano",
        "hallazgos": "",
        "observaciones": "Baño con shampoo neutro",
    }
    assert "Atención de Canela registrada; la cita quedó completada." in _texto(
        client.post(f"/estetica/citas/{cita_canela.pk}/atender/", registro, follow=True)
    )

    # 5. Recepción: por cobrar hoy están Toby, Max y Canela
    _entrar(client, "recepcion")
    toby = Cita.objects.get(mascota__nombre="Toby", mascota__cliente__telefono="8339990005")
    assert sorted(c.mascota.nombre for c in ventas.citas_por_cobrar()) == ["Canela", "Max", "Toby"]
    # Los botones Cobrar llevan el número de la cita sin separador de miles (DEF-008: «?cita=2,309» fallaba)
    lista = _texto(client.get("/ventas/"))
    for cita in (toby, cita_max, cita_canela):
        assert f"/ventas/nuevo/?cita={cita.pk}" in lista

    # 5a. Toby: consulta y desparasitante; efectivo con cambio
    desparasitante = Servicio.objects.get(nombre="Aplicación de desparasitante")
    lineas = _lineas((f"s-{toby.servicio_id}", 1), (f"s-{desparasitante.pk}", 1), iniciales=2)
    venta_toby = _cobrar_cita(client, toby, lineas, "750.00")
    assert "Entregue $50.00 de cambio. Ticket pagado." in _pagar(
        client, venta_toby, {"metodo": "Efectivo", "recibido": "800"}
    )

    # 5b. Max: sin el folio, el medicamento con control no se vende (RD-12); con el folio, sí
    cobro_vacuna = Servicio.objects.get(nombre="Aplicación de vacuna")
    propuesta = (f"s-{cita_max.servicio_id}", 1), (f"s-{cobro_vacuna.pk}", 1)
    sin_folio = _texto(
        client.post(
            f"/ventas/nuevo/?cita={cita_max.pk}",
            _lineas(*propuesta, (f"p-{amoxicilina.pk}", 14), iniciales=2),
            follow=True,
        )
    )
    assert "requiere receta: capture el folio de la receta (RD-12)" in sin_folio
    assert not Venta.objects.filter(cita=cita_max).exists()
    lineas = _lineas(*propuesta, (f"p-{amoxicilina.pk}", 14, folio_receta), iniciales=2)
    venta_max = _cobrar_cita(client, cita_max, lineas, "960.00")  # 400 + 350 + 14 × 15
    assert "Pago de $960.00 en tarjeta registrado. Ticket pagado." in _pagar(
        client, venta_max, {"metodo": "Tarjeta", "recibido": "960", "referencia": "AUT 4521"}
    )

    # 5c. Canela: baño por transferencia
    bano = _lineas((f"s-{cita_canela.servicio_id}", 1), iniciales=1)
    venta_canela = _cobrar_cita(client, cita_canela, bano, "350.00")
    assert "Pago de $350.00 en transferencia registrado. Ticket pagado." in _pagar(
        client, venta_canela, {"metodo": "Transferencia", "recibido": "350", "referencia": "SPEI 777"}
    )

    # 5d. Venta de mostrador a la clienta nueva: un collar en efectivo exacto
    collar = Producto.objects.get(codigo="ACC-001")
    contenido = _texto(
        client.post(f"/ventas/nuevo/?cliente={rosa.pk}", _lineas((f"p-{collar.pk}", 1)), follow=True)
    )
    assert f"Ticket {FOLIO}00006 generado por $150.00." in contenido
    venta_rosa = Venta.objects.get(folio_ticket=f"{FOLIO}00006")
    assert "Pago de $150.00 en efectivo registrado. Ticket pagado." in _pagar(
        client, venta_rosa, {"metodo": "Efectivo", "recibido": "150"}
    )

    # 5e. Pedro liquida su saldo de $260.00
    pedro = Venta.objects.get(folio_ticket=f"{FOLIO}00002")
    assert "Pago de $260.00 en efectivo registrado. Ticket pagado." in _pagar(
        client, pedro, {"metodo": "Efectivo", "recibido": "260"}
    )

    # 6. Cierre: nada por cobrar ni con saldo
    assert not list(ventas.citas_por_cobrar()) and not list(ventas.tickets_con_saldo())
    assert {v.estado for v in Venta.objects.all()} == {EstadoVenta.PAGADA}

    # 6a. El corte cuadra: efectivo 470 + 750 + 150 + 260; tarjeta 300 + 960; transferencia 350
    corte = _texto(client.get("/ventas/corte/"))
    assert (_neto(corte, "Efectivo"), _neto(corte, "Tarjeta"), _neto(corte, "Transferencia")) == (
        "$1,630.00",
        "$1,260.00",
        "$350.00",
    )
    assert "Recibido $1,710.00 · cambio entregado $80.00" in corte
    assert "data-total-neto>$3,240.00<" in corte
    resumen = ventas.corte_de_caja()
    assert resumen["tickets"]["generados"] == 6 and resumen["tickets"]["pagados"] == 6
    assert resumen["tickets"]["vendido"] == resumen["totales"]["neto"] == Decimal("3240.00")
    assert client.get("/ventas/corte/pdf/")["Content-Type"] == "application/pdf"

    # 6b. Inventario: la vacuna bajó una vez, la amoxicilina salió del lote que caduca primero y el collar
    # se descontó; cada lote cuadra con la suma de sus movimientos (RD-09)
    existencias = dict(Lote.objects.values_list("numero_lote", "cantidad_disponible"))
    assert (existencias["VAC-002-A"], existencias["MED-001-A"], existencias["MED-001-B"]) == (17, 6, 40)
    assert existencias["ACC-001-A"] == 10  # 12 − 1 del ticket de Jorge − 1 de Rosa
    for lote in Lote.objects.annotate(kardex=Sum("movimientos__cantidad")):
        assert lote.cantidad_disponible == (lote.kardex or 0), lote.numero_lote

    # 6c. Bitácora: cada cobro del día quedó registrado con la cuenta de Recepción (RNF-03)
    nuevos = BitacoraAuditoria.objects.filter(id_bitacora__gt=ultimo or 0).select_related("usuario")
    cobros = [r for r in nuevos if r.entidad == "pago"]
    assert len(cobros) == 5 and {r.usuario.nombre_usuario for r in cobros} == {"recepcion"}
    assert any(r.entidad == "consulta" and r.usuario.nombre_usuario == "veterinario" for r in nuevos)

    # 6d. Respaldo verificado al cierre (RNF-04)
    archivo, origen = _respaldar_base_de_pruebas()
    assert archivo.endswith("_TS10.bak") and origen == connection.settings_dict["NAME"]
