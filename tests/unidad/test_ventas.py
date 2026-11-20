"""S4-02 · Decisión D-20: folio del ticket consecutivo por año, T-AAAA-NNNNN."""

from datetime import date

import pytest

from catalogos.models import Puesto
from tests import fabricas
from ventas.models import Venta
from ventas.services import siguiente_folio

pytestmark = [pytest.mark.unidad, pytest.mark.django_db]


def test_S4_02_el_folio_es_consecutivo_y_reinicia_cada_ano():
    recepcion = fabricas.empleado(Puesto.RECEPCIONISTA, nombre="Sofía")
    cliente = fabricas.mascota().cliente
    assert siguiente_folio(date(2026, 11, 20)) == "T-2026-00001"
    for folio in ("T-2026-00001", "T-2026-00009", "T-2025-00040"):
        Venta.objects.create(folio_ticket=folio, cliente=cliente, empleado=recepcion)
    assert siguiente_folio(date(2026, 12, 31)) == "T-2026-00010"  # sigue al mayor del año
    assert siguiente_folio(date(2027, 1, 1)) == "T-2027-00001"  # cada año empieza en 1
