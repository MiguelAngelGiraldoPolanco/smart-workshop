"""Importe les assureurs depuis assureurs.json dans Insurer.

Le pourcentage de remise est extrait du texte 'remise_appliquee'
("12% (impacts uniquement)" -> 12.00). Le perimetre (discount_scope)
n'est pas present dans le JSON pour Allianz/MAIF : il provient de la
table du catalogue PDF (page 8), applique par nom d'assureur.
Idempotent via update_or_create sur 'name'.
"""
import json
import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Insurer

DEFAULT_PATH = Path(settings.BASE_DIR) / "public" / "assureurs.json"

# Perimetre de remise par assureur (source : catalogue PDF, page 8).
SCOPE_BY_NAME = {
    "Allianz France": Insurer.DiscountScope.PARE_BRISE_AVANT,
    "MAIF": Insurer.DiscountScope.PARE_BRISE_LUNETTE,
    "Macif": Insurer.DiscountScope.IMPACTS,
}


def parse_rate(text):
    """Extrait le pourcentage d'un texte : '12% (impacts)' -> Decimal('12.00')."""
    if not text:
        return Decimal("0.00")
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if not match:
        return Decimal("0.00")
    return Decimal(match.group(1).replace(",", "."))


class Command(BaseCommand):
    help = "Importe les assureurs depuis assureurs.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", default=str(DEFAULT_PATH),
            help="Chemin du fichier assureurs.json.",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {path}"))
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        created = updated = 0

        for row in data:
            name = row.get("nom", "").strip()
            if not name:
                continue
            scope = SCOPE_BY_NAME.get(name, Insurer.DiscountScope.TOUS)
            _, was_created = Insurer.objects.update_or_create(
                name=name,
                defaults={
                    "main_contact": row.get("contact_principal", ""),
                    "secondary_email": row.get("email_secondaire", ""),
                    "send_format": row.get("format_envoi", Insurer.SendFormat.EMAIL),
                    "portal_url": row.get("url_portail", ""),
                    "partner_code": row.get("code_partenaire", ""),
                    "discount_rate": parse_rate(row.get("remise_appliquee", "")),
                    "discount_scope": scope,
                    "notes": row.get("remarque", ""),
                    "active": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(
            f"Assureurs importes : {created} crees, {updated} mis a jour "
            f"({Insurer.objects.count()} au total)."
        ))
