"""S3-08 y S3-09 · UI-13 Receta por las pantallas y su PDF tamaño carta (RF-07, RD-08, D-18)."""

from decimal import Decimal
from io import BytesIO

import pytest
from django.utils import timezone
from pypdf import PdfReader

from catalogos.models import CategoriaServicio, Puesto
from clinico import services
from clinico.models import Receta
from inventario.models import Lote
from seguridad.models import Rol
from tests import fabricas

pytestmark = [pytest.mark.integracion, pytest.mark.django_db]


@pytest.fixture
def escenario(client):
    laura = fabricas.empleado(Puesto.VETERINARIO, cedula="12345678", nombre="Laura")
    client.force_login(fabricas.cuenta(laura, "laura", rol=Rol.VETERINARIO))
    cita = fabricas.cita_de_hoy(
        fabricas.paciente("Max", alergias="Penicilina"),
        laura,
        fabricas.servicio("Consulta general", CategoriaServicio.CONSULTA, 30),
    )
    consulta = services.abrir_consulta(cita, laura, {"sintomas": "Otitis", "peso_kg": Decimal("28")})
    amoxicilina = fabricas.producto(
        "MED-001", "Amoxicilina 250 mg", categoria="Medicamento", requiere_receta=True
    )
    lote = fabricas.lote(amoxicilina, 30)
    return client, consulta, amoxicilina, lote


def _datos(*filas, total=4):
    datos = {
        "indicaciones_generales": "Revisión en 7 días",
        "medicamentos-TOTAL_FORMS": str(total),
        "medicamentos-INITIAL_FORMS": "0",
        "medicamentos-MIN_NUM_FORMS": "4",
        "medicamentos-MAX_NUM_FORMS": "12",
    }
    for i in range(total):
        producto, dosis, frecuencia, dias = filas[i] if i < len(filas) else ("", "", "", "")
        datos.update(
            {
                f"medicamentos-{i}-producto": getattr(producto, "pk", producto),
                f"medicamentos-{i}-dosis": dosis,
                f"medicamentos-{i}-frecuencia": frecuencia,
                f"medicamentos-{i}-duracion_dias": dias,
                f"medicamentos-{i}-indicaciones": "",
            }
        )
    return datos


def test_S3_08_emitir_receta_desde_la_consulta_y_descargar_su_pdf(escenario):
    client, consulta, amoxicilina, lote = escenario
    url = f"/clinica/consultas/{consulta.pk}/receta/"
    assert "Alergias:" in client.get(url).content.decode()
    respuesta = client.post(url, _datos((amoxicilina, "1 tableta", "Cada 12 horas", 7)), follow=True)
    folio = f"R-{timezone.localdate():%Y}-00001"
    contenido = respuesta.content.decode()
    assert f"Receta {folio} emitida." in contenido and f'data-receta="{folio}"' in contenido
    assert Lote.objects.get(pk=lote.pk).cantidad_disponible == Decimal("30")  # la receta no descuenta

    pdf = client.get(f"/clinica/recetas/{Receta.objects.get().pk}/pdf/")
    assert pdf["Content-Type"] == "application/pdf" and f"Receta-{folio}.pdf" in pdf["Content-Disposition"]
    pagina = PdfReader(BytesIO(pdf.content)).pages[0]
    texto = pagina.extract_text()
    assert folio in texto and "Amoxicilina 250 mg" in texto and "Cada 12 horas" in texto
    assert "12345678" in texto and "Penicilina" in texto  # cédula del veterinario y alergias
    assert (round(float(pagina.mediabox.width)), round(float(pagina.mediabox.height))) == (612, 792)


def test_S3_08_validaciones_de_la_receta(escenario):
    client, consulta, amoxicilina, _ = escenario
    url = f"/clinica/consultas/{consulta.pk}/receta/"
    assert "Agregue al menos un medicamento" in client.post(url, _datos()).content.decode()
    assert (
        "Capture la frecuencia."
        in client.post(url, _datos((amoxicilina, "1 tableta", "", 7))).content.decode()
    )
    assert not Receta.objects.exists()


def test_S3_09_el_administrador_descarga_la_receta_y_recepcion_no(escenario, crear_usuario):
    client, consulta, amoxicilina, _ = escenario
    receta = services.emitir_receta(consulta, consulta.empleado, [(amoxicilina, "1", "Cada 8 h", 5, None)])
    client.force_login(crear_usuario("administrador", rol=Rol.ADMINISTRADOR))
    assert client.get(f"/clinica/recetas/{receta.pk}/pdf/").status_code == 200
    assert client.get(f"/clinica/consultas/{consulta.pk}/receta/").status_code == 403  # ○: no emite
    client.force_login(crear_usuario("recepcion", rol=Rol.RECEPCIONISTA))
    assert client.get(f"/clinica/recetas/{receta.pk}/pdf/").status_code == 403
