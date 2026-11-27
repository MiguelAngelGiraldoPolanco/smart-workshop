"""Tests des vues : authentification, alta client, devis, facture, recherche."""
from decimal import Decimal

import pytest

from core.models import Client, Invoice, Quote, Service, Vehicle


@pytest.mark.django_db
def test_login_required(client):
    """Sad path : un anonyme est redirige vers la connexion."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_dashboard_ok(auth_client):
    """Happy path : le tableau de bord s'affiche pour un utilisateur connecte."""
    response = auth_client.get("/")
    assert response.status_code == 200
    assert "Tableau de bord" in response.content.decode()


@pytest.mark.django_db
def test_client_create_happy(auth_client):
    response = auth_client.post("/clients/nouveau/", {
        "name": "Jean Test", "email": "jean@test.fr", "phone": "0612345678",
        "license_plate": "ZZ-001-ZZ", "brand": "Renault", "model": "Clio",
        "year": "2020", "vin": "",
    })
    assert response.status_code == 302
    assert Vehicle.objects.filter(license_plate="ZZ-001-ZZ").exists()


@pytest.mark.django_db
def test_client_create_sad_missing_name(auth_client):
    """Sad path : sans nom, le formulaire est rejete et rien n'est cree."""
    response = auth_client.post("/clients/nouveau/", {
        "name": "", "license_plate": "ZZ-002-ZZ", "brand": "R", "model": "C",
    })
    assert response.status_code == 200  # re-affiche avec erreurs
    assert not Vehicle.objects.filter(license_plate="ZZ-002-ZZ").exists()


@pytest.mark.django_db
def test_quote_create_and_invoice(auth_client, seed_catalog):
    """Happy path : creation d'un devis puis conversion en facture."""
    pb = Service.objects.get(code="PB_AVANT_STD")
    response = auth_client.post("/devis/nouveau/", {
        "license_plate": "QQ-001-QQ", "client_name": "Devis Test",
        "brand": "Peugeot", "model": "208", "services": [pb.pk], "discount": "0",
    })
    assert response.status_code == 302
    quote = Quote.objects.get()
    assert quote.total_ttc == Decimal("300.00")  # 250 HT + TVA 20%

    auth_client.post(f"/devis/{quote.pk}/facturer/")
    invoice = Invoice.objects.get(quote=quote)
    assert invoice.number == "FAC-00001"
    quote.refresh_from_db()
    assert quote.status == Quote.Status.FACTURE


@pytest.mark.django_db
def test_quote_create_sad_no_service(auth_client, seed_catalog):
    """Sad path : un devis sans service est rejete."""
    response = auth_client.post("/devis/nouveau/", {
        "license_plate": "QQ-002-QQ", "client_name": "X",
        "brand": "P", "model": "208", "discount": "0",
    })
    assert response.status_code == 200
    assert Quote.objects.count() == 0


@pytest.mark.django_db
def test_search_found_and_not_found(auth_client):
    cli = Client.objects.create(name="Dupont Cherche")
    Vehicle.objects.create(client=cli, license_plate="SR-001-CH", brand="R", model="C")

    found = auth_client.get("/recherche/?q=Dupont")
    assert "Dupont Cherche" in found.content.decode()

    empty = auth_client.get("/recherche/?q=ZZZINEXISTANT")
    assert "Aucun resultat" in empty.content.decode()
