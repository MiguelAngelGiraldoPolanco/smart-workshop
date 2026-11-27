"""Tests des modeles : calcul des totaux et perimetre de remise."""
from decimal import Decimal

import pytest

from core.models import Client, Insurer, Quote, QuoteItem, Service, Vehicle


def _service(code, price, **kw):
    return Service.objects.create(
        code=code, name=code, category=Service.Category.PARE_BRISE,
        price=Decimal(price), **kw,
    )


@pytest.mark.django_db
def test_recalc_with_insurer_scope():
    """Happy path : la remise assureur ne s'applique qu'aux actes du perimetre."""
    cli = Client.objects.create(name="X")
    veh = Vehicle.objects.create(client=cli, license_plate="AA-111-AA", brand="R", model="C")
    ins = Insurer.objects.create(
        name="Allianz", main_contact="x", discount_rate=Decimal("10"),
        discount_scope=Insurer.DiscountScope.PARE_BRISE_AVANT,
    )
    q = Quote.objects.create(client=cli, vehicle=veh, insurer=ins)
    pb = _service("PB_AVANT_STD", "250.00")
    supp = _service("PB_TEINTE", "45.00", is_supplement=True)
    QuoteItem.objects.create(quote=q, service=pb, unit_price=pb.price)
    QuoteItem.objects.create(quote=q, service=supp, unit_price=supp.price)

    q.recalc_total()

    # Remise = 10% de 250 (le supplement est exclu) = 25 ; brut 295 -> HT 270.
    assert q.subtotal_ht == Decimal("270.00")
    assert q.vat_amount == Decimal("54.00")
    assert q.total_ttc == Decimal("324.00")


@pytest.mark.django_db
def test_recalc_without_insurer():
    """Sans assureur ni remise, le sous-total egale le brut."""
    cli = Client.objects.create(name="Y")
    veh = Vehicle.objects.create(client=cli, license_plate="BB-222-BB", brand="R", model="C")
    q = Quote.objects.create(client=cli, vehicle=veh)
    s = _service("IMPACT_RES", "80.00")
    QuoteItem.objects.create(quote=q, service=s, unit_price=s.price)

    q.recalc_total()

    assert q.subtotal_ht == Decimal("80.00")
    assert q.total_ttc == Decimal("96.00")


def test_applies_to_scope():
    """Sad path : un assureur 'impacts' ne s'applique pas a un pare-brise."""
    ins = Insurer(discount_scope=Insurer.DiscountScope.IMPACTS)
    assert ins.applies_to(Service(code="IMPACT_RES")) is True
    assert ins.applies_to(Service(code="PB_AVANT_STD")) is False
