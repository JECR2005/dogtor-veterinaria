"""Servicios (reglas de negocio) del componente «Ventas y caja».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P4:

- RF-13, RD-06 y RD-11: tickets, pagos parciales con cambio, precio histórico y corte de caja (P4).
- RD-12: producto con control solo con folio de receta válido (P4).
- RF-14: cancelación con permisos según haya pagos; reintegro de productos vendidos (P4).

D-20: el folio del ticket es consecutivo por año, T-AAAA-NNNNN (como el de las recetas); lo aplicado en
consulta se cobra con un servicio de la categoría Aplicación y no vuelve a descontar el lote (RD-09).
"""

from django.utils import timezone

from .models import Venta

PREFIJO_FOLIO = "T"


def siguiente_folio(hoy=None):
    """D-20 · Siguiente folio del año: T-2026-00001, T-2026-00002…

    Se toma dentro de la transacción del ticket; si dos tickets tomaran el mismo a la vez,
    UQ_venta_folio_ticket rechaza el segundo y se reintenta.
    """
    hoy = hoy or timezone.localdate()
    prefijo = f"{PREFIJO_FOLIO}-{hoy:%Y}-"
    ultimos = Venta.objects.filter(folio_ticket__startswith=prefijo).values_list("folio_ticket", flat=True)
    numero = max((int(folio.rsplit("-", 1)[1]) for folio in ultimos), default=0) + 1
    return f"{prefijo}{numero:05d}"
