"""S5-16 · TS-11: guarda la agenda del día en PDF, lista para imprimir si falla la luz o la red (R07).

Uso (lo ejecuta cada mañana la tarea «Agenda del dia», scripts/programar_tareas.ps1):
    python manage.py generar_agenda                    # hoy, en AGENDA_DIR (defecto logs/agenda)
    python manage.py generar_agenda --fecha 2026-11-23 --salida C:\\Dogtor\\Agenda

Conserva los PDF de los últimos 30 días. El archivo no necesita el servidor para abrirse ni imprimirse.
"""

import os
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda import services
from reportes.services import pdf_desde_plantilla

DIAS_CONSERVADOS = 30


class Command(BaseCommand):
    help = "Genera el PDF de la agenda del día para la contingencia sin sistema (TS-11, R07)."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=date.fromisoformat, help="Día (AAAA-MM-DD); defecto hoy.")
        parser.add_argument(
            "--salida",
            default=os.environ.get("AGENDA_DIR") or str(Path(settings.BASE_DIR) / "logs" / "agenda"),
            help="Carpeta donde se guarda el PDF.",
        )

    def handle(self, *args, **opciones):
        fecha = opciones["fecha"] or timezone.localdate()
        carpeta = Path(os.path.expandvars(opciones["salida"]))
        carpeta.mkdir(parents=True, exist_ok=True)
        citas = list(services.agenda_para_imprimir(fecha))
        archivo = carpeta / f"Agenda-{fecha:%Y-%m-%d}.pdf"
        archivo.write_bytes(pdf_desde_plantilla("reportes/agenda.html", {"fecha": fecha, "citas": citas}))
        limite = datetime.now() - timedelta(days=DIAS_CONSERVADOS)
        for viejo in carpeta.glob("Agenda-*.pdf"):
            if datetime.fromtimestamp(viejo.stat().st_mtime) < limite:
                viejo.unlink()
        self.stdout.write(self.style.SUCCESS(f"Agenda del {fecha:%d/%m/%Y}: {len(citas)} citas en {archivo}"))
