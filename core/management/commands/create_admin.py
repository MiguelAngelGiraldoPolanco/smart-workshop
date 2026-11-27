"""Cree (ou met a jour) le superutilisateur root / password.

set_password contourne les validateurs de mot de passe (qui refuseraient
'password' en interactif). Idempotent.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

USERNAME = "root"
PASSWORD = "password"


class Command(BaseCommand):
    help = "Cree ou reinitialise le superutilisateur root / password."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=USERNAME)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(PASSWORD)
        user.save()

        verb = "cree" if created else "mis a jour"
        self.stdout.write(self.style.SUCCESS(
            f"Superutilisateur '{USERNAME}' {verb} (mot de passe : {PASSWORD})."
        ))
