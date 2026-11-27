"""Importe l'historique des reparations (reparations.csv).

Regroupement par immatriculation (PAS par email : il y a des typos).
Cree Client (dedoublonne par nom) + Vehicle (par plaque) + RepairHistory
(une par ligne). Telephones normalises au format FR '06 12 34 56 78'.
Email/telephone vides -> laisses en blanc, sans echec. Idempotent.
"""
import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Client, RepairHistory, Vehicle

DEFAULT_PATH = Path(settings.BASE_DIR) / "public" / "reparations.csv"


def normalize_phone(raw):
    """'06 23 45 67 89' / '06.34.56.78.90' -> '06 12 34 56 78'."""
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if len(digits) == 10:
        return " ".join(digits[i:i + 2] for i in range(0, 10, 2))
    return digits  # format inattendu : on garde les chiffres tels quels


def parse_amount(raw):
    try:
        return Decimal((raw or "0").strip())
    except (InvalidOperation, AttributeError):
        return Decimal("0.00")


class Command(BaseCommand):
    help = "Importe l'historique des reparations depuis reparations.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", default=str(DEFAULT_PATH),
            help="Chemin du fichier reparations.csv.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {path}"))
            return

        clients = vehicles = repairs = 0

        with path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                plate = (row.get("immatriculation") or "").strip()
                name = (row.get("client_nom") or "").strip()
                if not plate or not name:
                    continue

                email = (row.get("client_email") or "").strip()
                phone = normalize_phone(row.get("client_tel"))

                # Client : dedoublonne par nom (les emails ont des typos).
                client, c_created = Client.objects.get_or_create(
                    name=name, defaults={"email": email, "phone": phone},
                )
                clients += c_created
                # Complete les coordonnees si elles manquaient.
                changed = False
                if not client.email and email:
                    client.email, changed = email, True
                if not client.phone and phone:
                    client.phone, changed = phone, True
                if changed:
                    client.save(update_fields=["email", "phone"])

                # Vehicle : un par plaque.
                vehicle, v_created = Vehicle.objects.get_or_create(
                    license_plate=plate,
                    defaults={
                        "client": client,
                        "brand": (row.get("marque") or "").strip(),
                        "model": (row.get("modele") or "").strip(),
                    },
                )
                vehicles += v_created

                # RepairHistory : une par intervention (idempotent sur la cle naturelle).
                _, r_created = RepairHistory.objects.get_or_create(
                    vehicle=vehicle,
                    date=date.fromisoformat(row["date"].strip()),
                    intervention_text=(row.get("intervention") or "").strip(),
                    amount_ht=parse_amount(row.get("montant_ht")),
                    defaults={
                        "client": client,
                        "status_text": (row.get("statut") or "").strip(),
                        "notes": (row.get("notes") or "").strip(),
                        "is_legacy": True,
                    },
                )
                repairs += r_created

        self.stdout.write(self.style.SUCCESS(
            f"Reparations importees : {clients} clients, {vehicles} vehicules, "
            f"{repairs} interventions creees."
        ))
