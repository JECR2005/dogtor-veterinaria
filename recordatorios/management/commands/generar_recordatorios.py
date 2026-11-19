"""RF-09 · Genera la lista de recordatorios del día (para el Programador de tareas de Windows en P5).

Uso: python manage.py generar_recordatorios
La lista también se genera sola al abrir Recordatorios o el Inicio de Recepción; este comando sirve para
tenerla lista antes de que llegue el personal.
"""

from django.core.management.base import BaseCommand

from recordatorios import services


class Command(BaseCommand):
    help = "Genera los recordatorios del día: próximas dosis a 3 días y citas de mañana (RF-09)."

    def handle(self, *args, **opciones):
        creados = services.generar()
        self.stdout.write(self.style.SUCCESS(f"Recordatorios nuevos: {creados}."))
