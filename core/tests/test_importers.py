"""Tests des importateurs (catalogue, assureurs, reparations)."""
from decimal import Decimal

import pytest
from django.core.management import call_command

from core.models import Client, Insurer, RepairHistory, Service, Vehicle


@pytest.mark.django_db
def test_import_catalog_idempotent(seed_catalog):
    """Happy path : 43 services, et reimporter ne cree pas de doublons."""
    assert Service.objects.count() == 43
    call_command("import_catalog")
    assert Service.objects.count() == 43
    # Quelques proprietes attendues.
    assert Service.objects.get(code="PB_AVANT_PL").price_on_request is True
    assert Service.objects.get(code="PB_TEINTE").is_supplement is True


@pytest.mark.django_db
def test_import_insurers(seed_insurers):
    """Le taux est extrait du texte et le perimetre est correct."""
    assert Insurer.objects.count() == 3
    macif = Insurer.objects.get(name="Macif")
    assert macif.discount_rate == Decimal("12.00")
    assert macif.discount_scope == Insurer.DiscountScope.IMPACTS
    assert macif.secondary_email == "indemnisation.toulouse@macif.fr"


@pytest.mark.django_db
def test_import_reparations():
    """Regroupement par plaque, dedup client, telephone normalise."""
    call_command("import_reparations")
    assert Client.objects.count() == 16
    assert Vehicle.objects.count() == 16
    assert RepairHistory.objects.count() == 20

    dupont = Client.objects.get(name="Martin Dupont")
    assert dupont.repairs.count() == 4
    assert dupont.email == "m.dupont@gmail.com"   # le typo gmial est ignore
    assert dupont.phone == "06 12 34 56 78"       # normalise

    # Sad input : email manquant -> laisse vide, sans echec.
    assert Client.objects.get(name="Mme Bernard").email == ""
