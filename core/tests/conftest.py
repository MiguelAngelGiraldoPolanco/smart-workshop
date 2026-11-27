"""Fixtures partagees pour les tests."""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command


@pytest.fixture
def seed_catalog(db):
    """Catalogue importe (43 services)."""
    call_command("import_catalog")


@pytest.fixture
def seed_insurers(db):
    """Assureurs importes (3)."""
    call_command("import_insurers")


@pytest.fixture
def admin_user(db):
    """Superutilisateur root cree par create_admin."""
    call_command("create_admin")
    return get_user_model().objects.get(username="root")


@pytest.fixture
def auth_client(client, admin_user):
    """Client de test deja connecte."""
    client.force_login(admin_user)
    return client
