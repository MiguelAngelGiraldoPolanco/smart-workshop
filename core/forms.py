"""Formulaires d'AtelierVitre.

Libelles en francais, widgets larges (form-control-lg) pour la lisibilite
(Pascal et Marc ont +50 ans).
"""
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Client, Insurer, Service, Vehicle

# Classes Bootstrap reutilisees pour des champs larges et lisibles.
TEXT = {"class": "form-control form-control-lg"}
SELECT = {"class": "form-select form-select-lg"}


class LoginForm(AuthenticationForm):
    """Formulaire de connexion avec champs larges."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(TEXT)
        self.fields["password"].widget.attrs.update(TEXT)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email", "phone"]
        widgets = {
            "name": forms.TextInput(attrs=TEXT),
            "email": forms.EmailInput(attrs=TEXT),
            "phone": forms.TextInput(attrs=TEXT),
        }


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["license_plate", "brand", "model", "year", "vin"]
        widgets = {
            "license_plate": forms.TextInput(attrs=TEXT),
            "brand": forms.TextInput(attrs=TEXT),
            "model": forms.TextInput(attrs=TEXT),
            "year": forms.NumberInput(attrs=TEXT),
            "vin": forms.TextInput(attrs=TEXT),
        }


class ServiceMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Affiche le nom et le prix de chaque service dans la case a cocher."""

    def label_from_instance(self, service):
        return f"{service.name} — {service.price} €"


class QuoteForm(forms.Form):
    """Creation d'un devis : plaque (existante ou nouvelle) + services.

    Si la plaque existe, le vehicule et le client sont reutilises. Sinon,
    les champs client/vehicule deviennent obligatoires pour les creer.
    """

    license_plate = forms.CharField(
        label="Immatriculation", max_length=20,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "AB-123-CD"}),
    )
    # Champs utilises uniquement si la plaque n'existe pas encore.
    client_name = forms.CharField(
        label="Nom du client", max_length=200, required=False,
        widget=forms.TextInput(attrs=TEXT),
    )
    client_email = forms.EmailField(
        label="Email", required=False, widget=forms.EmailInput(attrs=TEXT),
    )
    client_phone = forms.CharField(
        label="Telephone", max_length=30, required=False,
        widget=forms.TextInput(attrs=TEXT),
    )
    brand = forms.CharField(
        label="Marque", max_length=80, required=False,
        widget=forms.TextInput(attrs=TEXT),
    )
    model = forms.CharField(
        label="Modele", max_length=80, required=False,
        widget=forms.TextInput(attrs=TEXT),
    )
    year = forms.IntegerField(
        label="Annee", required=False, widget=forms.NumberInput(attrs=TEXT),
    )

    insurer = forms.ModelChoiceField(
        label="Assureur (optionnel)", required=False,
        queryset=Insurer.objects.filter(active=True),
        widget=forms.Select(attrs=SELECT),
    )
    services = ServiceMultipleChoiceField(
        label="Services",
        queryset=Service.objects.filter(active=True, price_on_request=False)
        .order_by("category", "code"),
        widget=forms.CheckboxSelectMultiple,
    )
    discount = forms.DecimalField(
        label="Remise manuelle (HT)", required=False, min_value=Decimal("0"),
        max_digits=10, decimal_places=2, initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs=TEXT),
    )
    notes = forms.CharField(
        label="Notes", required=False,
        widget=forms.Textarea(attrs={**TEXT, "rows": 2}),
    )

    def clean(self):
        cleaned = super().clean()
        plate = (cleaned.get("license_plate") or "").strip()
        if not plate:
            return cleaned

        self.existing_vehicle = Vehicle.objects.filter(license_plate=plate).first()
        if self.existing_vehicle is None:
            # Nouveau vehicule : nom du client, marque et modele requis.
            missing = []
            if not cleaned.get("client_name"):
                missing.append("client_name")
            if not cleaned.get("brand"):
                missing.append("brand")
            if not cleaned.get("model"):
                missing.append("model")
            for field in missing:
                self.add_error(
                    field,
                    "Obligatoire pour creer un nouveau vehicule.",
                )
        return cleaned


class DateRangeForm(forms.Form):
    """Filtre de periode pour le rapport des ventes."""

    date_from = forms.DateField(
        label="Du", required=False,
        widget=forms.DateInput(attrs={**TEXT, "type": "date"}),
    )
    date_to = forms.DateField(
        label="Au", required=False,
        widget=forms.DateInput(attrs={**TEXT, "type": "date"}),
    )
