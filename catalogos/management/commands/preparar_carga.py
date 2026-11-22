"""S5-14 · Prepara los datos de la prueba de carga TS-06 (Locust) y anota sus números en logs/carga.json.

Uso (después de `cargar_datos_prueba --mascotas 1200 --historial 30`):
    python manage.py preparar_carga

- Un producto «CARGA-001» con un lote amplio: cada ticket de la carga vende una pieza (RD-05, con bloqueo).
- Consultas ABIERTAS de hoy para la cuenta `veterinario`, una por cada usuario veterinario de Locust, en
  mascotas distintas (que no son de los escenarios): los usuarios las guardan una y otra vez (RF-06).
- 50 clientes activos a los que la recepcionista cobra.

Es repetible: reutiliza el producto y las consultas abiertas que ya existan. Solo corre donde se permiten
datos ficticios (cláusula Undécima).
"""

import json
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from agenda.models import Cita, EstadoCita
from catalogos.models import CategoriaProducto, Cliente, Mascota, Producto, Servicio
from clinico import services as clinico
from clinico.models import Consulta, EstadoConsulta
from inventario.models import Lote, MovimientoInventario, TipoMovimiento
from seguridad.models import Usuario

MOTIVO = "Carga TS-06"
CODIGO = "CARGA-001"
TELEFONOS_DE_ESCENARIOS = "833999"


class Command(BaseCommand):
    help = "Prepara consultas abiertas, un producto y clientes para la prueba de carga TS-06 (Locust)."

    def add_arguments(self, parser):
        parser.add_argument("--consultas", type=int, default=10, help="Consultas abiertas (defecto 10).")
        parser.add_argument(
            "--salida", default=str(Path(settings.BASE_DIR) / "logs" / "carga.json"), help="Archivo JSON."
        )

    def handle(self, *args, **opciones):
        if not getattr(settings, "DOGTOR_PERMITIR_DATOS_PRUEBA", False):
            raise CommandError("Este comando no se ejecuta en producción (cláusula Undécima).")
        veterinaria = Usuario.objects.select_related("empleado").get(nombre_usuario="veterinario").empleado
        administrador = (
            Usuario.objects.select_related("empleado").get(nombre_usuario="administrador").empleado
        )
        generales = Mascota.objects.exclude(cliente__telefono__startswith=TELEFONOS_DE_ESCENARIOS).filter(
            cliente__activo=True
        )
        if generales.count() < opciones["consultas"] + 50:
            raise CommandError("Faltan mascotas: ejecute antes cargar_datos_prueba --mascotas 1200.")

        with transaction.atomic():
            producto = self._producto(administrador)
            consultas = self._consultas(veterinaria, generales, opciones["consultas"])

        clientes = list(
            Cliente.objects.filter(activo=True)
            .exclude(telefono__startswith=TELEFONOS_DE_ESCENARIOS)
            .order_by("pk")
            .values_list("pk", flat=True)[:50]
        )
        datos = {
            "generado": timezone.localtime().isoformat(timespec="seconds"),
            "mascotas": Mascota.objects.count(),
            "producto": f"p-{producto.pk}",
            "servicio": f"s-{Servicio.objects.get(nombre='Consulta general').pk}",
            "clientes": clientes,
            "consultas": [{"id": c.pk, "mascota": c.expediente.mascota_id} for c in consultas],
        }
        salida = Path(opciones["salida"])
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Carga lista: {len(consultas)} consultas abiertas, {len(clientes)} clientes, producto "
                f"{CODIGO} y {datos['mascotas']} mascotas. Datos en {salida}"
            )
        )

    def _producto(self, administrador):
        producto, creado = Producto.objects.get_or_create(
            codigo=CODIGO,
            defaults={
                "nombre": "Artículo de la prueba de carga (TS-06)",
                "categoria": CategoriaProducto.ACCESORIO,
                "unidad_medida": "Pieza",
                "precio_venta": Decimal("50.00"),
                "stock_minimo": 0,
            },
        )
        if creado:
            lote = Lote.objects.create(producto=producto, numero_lote="CARGA-A", cantidad_disponible=100_000)
            MovimientoInventario.objects.create(
                lote=lote,
                empleado=administrador,
                tipo=TipoMovimiento.ENTRADA,
                cantidad=100_000,
                referencia=MOTIVO,
            )
        return producto

    def _consultas(self, veterinaria, generales, cuantas):
        hoy = timezone.localdate()
        abiertas = list(
            Consulta.objects.filter(
                cita__motivo=MOTIVO, cita__fecha_hora_inicio__date=hoy, estado=EstadoConsulta.ABIERTA
            ).select_related("expediente")
        )
        servicio = Servicio.objects.get(nombre="Consulta general")
        usadas = {c.expediente.mascota_id for c in abiertas}
        candidatas = generales.exclude(pk__in=usadas).filter(citas__isnull=True).order_by("pk")
        for mascota in candidatas[: max(0, cuantas - len(abiertas))]:
            # Una hora fuera del horario (7:00) para no estorbar la agenda del día; la cita se crea directo
            inicio = timezone.make_aware(datetime.combine(hoy, time(7))) + timedelta(minutes=len(abiertas))
            cita = Cita.objects.create(
                mascota=mascota,
                empleado=veterinaria,
                servicio=servicio,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=inicio + timedelta(minutes=servicio.duracion_min),
                estado=EstadoCita.PROGRAMADA,
                motivo=MOTIVO,
            )
            abiertas.append(
                clinico.abrir_consulta(cita, veterinaria, {"sintomas": "Revisión", "peso_kg": Decimal("10")})
            )
        return abiertas
