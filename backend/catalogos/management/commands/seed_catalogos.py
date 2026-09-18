"""Siembra el catalogo fijo de regiones y entidades. Idempotente."""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalogos.models import Entidad, Region

# Fuente: boveda Obsidian, "Ref - Regiones Operativas IMSS-Bienestar".
# Cada entidad pertenece a UNA sola region.
REGIONES = [
    ("Centro", ["Ciudad de México", "Estado de México", "Hidalgo"]),
    ("Noreste", ["San Luis Potosí", "Tamaulipas", "Veracruz", "Zacatecas"]),
    ("Noroeste", ["Baja California", "Baja California Sur", "Colima", "Nayarit",
                  "Sinaloa", "Sonora"]),
    ("Sureste", ["Campeche", "Chiapas", "Oaxaca", "Quintana Roo", "Tabasco",
                 "Yucatán"]),
    ("Suroeste", ["Guerrero", "Michoacán", "Morelos", "Puebla", "Tlaxcala"]),
]


class Command(BaseCommand):
    help = "Crea o actualiza las 5 regiones operativas y sus 24 entidades."

    @transaction.atomic
    def handle(self, *args, **opciones):
        total_entidades = 0
        for orden, (nombre_region, entidades) in enumerate(REGIONES, start=1):
            region, _ = Region.objects.update_or_create(
                clave=slugify(nombre_region),
                defaults={"nombre": nombre_region, "orden": orden},
            )
            for nombre_entidad in entidades:
                Entidad.objects.update_or_create(
                    clave=slugify(nombre_entidad),
                    defaults={"nombre": nombre_entidad, "region": region, "activa": True},
                )
                total_entidades += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogos sembrados: {len(REGIONES)} regiones, {total_entidades} entidades."
            )
        )
