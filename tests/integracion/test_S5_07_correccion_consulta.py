"""S5-07 · El Administrador corrige una consulta firmada, con motivo y registro en bitácora (RD-07, RNF-03).

Criterios del plan: la corrección guarda los valores previos; nadie más puede corregir. La consulta sigue
firmada y la base la sigue protegiendo después de la corrección (la puerta de D-19 se cierra al terminar).
"""

from decimal import Decimal

import pytest
from django.db import DatabaseError, transaction

from catalogos.models import CategoriaServicio, Mascota, Puesto
from clinico import services
from clinico.models import Consulta
from seguridad import bitacora
from seguridad.models import AccionBitacora, BitacoraAuditoria, Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]

DATOS = {
    "sintomas": "Revisión",
    "peso_kg": "28.40",
    "temperatura_c": "38.6",
    "diagnostico": "Sano",
    "tratamiento": "",
    "observaciones": "",
}


@pytest.fixture
def firmada():
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    max_ = fabricas.paciente("Max")
    cita = fabricas.cita_de_hoy(
        max_, laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    datos = {"sintomas": "Revisión", "peso_kg": Decimal("284.0"), "diagnostico": "Sano"}
    consulta = services.abrir_consulta(cita, laura, datos)
    services.firmar(consulta, laura)  # el peso se capturó con un dígito de más
    return laura, max_, Consulta.objects.get(pk=consulta.pk)


def test_S5_07_el_administrador_corrige_con_motivo_y_la_bitacora_guarda_lo_anterior(
    client, crear_usuario, firmada
):
    _, max_, consulta = firmada
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    client.force_login(admin)
    pantalla = client.get(f"/clinica/consultas/{consulta.pk}/").content.decode()
    assert "Corregir (Administrador)" in pantalla

    sin_motivo = client.post(f"/clinica/consultas/{consulta.pk}/corregir/", {**DATOS, "motivo": "peso"})
    assert "al menos 10 caracteres" in sin_motivo.content.decode()
    assert Consulta.objects.get(pk=consulta.pk).peso_kg == Decimal("284.00")

    motivo = "El veterinario capturó el peso con un dígito de más"
    respuesta = client.post(
        f"/clinica/consultas/{consulta.pk}/corregir/", {**DATOS, "motivo": motivo}, follow=True
    )
    assert "Consulta corregida" in respuesta.content.decode()
    corregida = Consulta.objects.get(pk=consulta.pk)
    assert (corregida.estado, corregida.peso_kg, corregida.temperatura_c) == (
        "Firmada",
        Decimal("28.40"),
        Decimal("38.6"),
    )
    assert Mascota.objects.get(pk=max_.pk).peso_actual == Decimal("28.40")  # era su última consulta firmada

    registro = BitacoraAuditoria.objects.filter(entidad="consulta", usuario=admin).get()
    assert registro.accion == AccionBitacora.MODIFICACION and registro.id_registro == consulta.pk
    previos = bitacora.valores_previos(registro)
    assert previos["peso_kg"] == "284.00" and previos["temperatura_c"] is None
    assert previos[services.CLAVE_MOTIVO] == motivo
    assert motivo in respuesta.content.decode()  # la consulta muestra sus correcciones

    # La puerta se cerró: un cambio directo vuelve a rechazarse (RD-07)
    with pytest.raises(DatabaseError, match="RD-07"), transaction.atomic():
        Consulta.objects.filter(pk=consulta.pk).update(diagnostico="Otro")


def test_S5_07_reglas_de_la_correccion(crear_usuario, firmada):
    laura, max_, consulta = firmada
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    datos = {**DATOS, "peso_kg": Decimal("28.40"), "temperatura_c": None}
    with pytest.raises(services.ErrorClinico, match="Solo el Administrador"):
        services.corregir_consulta(consulta, laura.usuario, datos, "Motivo suficientemente largo")
    with pytest.raises(services.ErrorClinico, match="motivo"):
        services.corregir_consulta(consulta, admin, datos, "corto")
    with pytest.raises(services.ErrorClinico, match="conserva síntomas, peso y diagnóstico"):
        services.corregir_consulta(
            consulta, admin, {**datos, "diagnostico": " "}, "Motivo suficientemente largo"
        )
    services.corregir_consulta(consulta, admin, datos, "Peso con un dígito de más")
    with pytest.raises(services.ErrorClinico, match="No hay cambios"):
        services.corregir_consulta(consulta, admin, datos, "Peso con un dígito de más")

    # Si no es la consulta firmada más reciente, el peso actual de la mascota no cambia
    cita = fabricas.cita_de_hoy(max_, laura, consulta.cita.servicio, "12:00")
    nueva = services.abrir_consulta(
        cita, laura, {"sintomas": "Control", "peso_kg": Decimal("29"), "diagnostico": "Sano"}
    )
    services.firmar(nueva, laura)
    services.corregir_consulta(
        consulta, admin, {**datos, "peso_kg": Decimal("28.50")}, "Ajuste de la báscula"
    )
    assert Mascota.objects.get(pk=max_.pk).peso_actual == Decimal("29.00")


def test_S5_07_una_consulta_abierta_no_se_corrige(crear_usuario, client):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    cita = fabricas.cita_de_hoy(
        fabricas.paciente("Max"), laura, fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30)
    )
    abierta = services.abrir_consulta(cita, laura, {"sintomas": "Tos", "peso_kg": Decimal("10")})
    admin = crear_usuario("admin", rol=Rol.ADMINISTRADOR)
    client.force_login(admin)
    pantalla = client.get(f"/clinica/consultas/{abierta.pk}/corregir/")
    assert pantalla.status_code == 200 and "sigue abierta" in pantalla.content.decode()
    with pytest.raises(services.ErrorClinico, match="sigue abierta"):
        services.corregir_consulta(abierta, admin, DATOS, "Motivo suficientemente largo")


@pytest.mark.parametrize("rol", [Rol.VETERINARIO, Rol.ESTILISTA, Rol.RECEPCIONISTA])
def test_S5_07_nadie_mas_corrige(client, crear_usuario, firmada, rol):
    _, _, consulta = firmada
    client.force_login(crear_usuario("otro", rol=rol))
    url = f"/clinica/consultas/{consulta.pk}/corregir/"
    assert client.get(url).status_code == 403
    assert client.post(url, {**DATOS, "motivo": "Intento de corrección"}).status_code == 403
    assert Consulta.objects.get(pk=consulta.pk).peso_kg == Decimal("284.00")
