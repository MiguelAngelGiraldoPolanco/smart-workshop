"""Modeles de domaine d'AtelierVitre.

Convention : noms de champs/modeles en anglais ; libelles visibles
(verbose_name, __str__) en francais. L'argent est toujours en Decimal.
"""
from decimal import Decimal

from django.db import models

# Quantisation monetaire : 2 decimales.
CENTS = Decimal("0.01")


class Client(models.Model):
    """Un client du garage (particulier ou societe)."""

    name = models.CharField("Nom", max_length=200)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Telephone", max_length=30, blank=True)
    created = models.DateTimeField("Cree le", auto_now_add=True)
    updated = models.DateTimeField("Mis a jour le", auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    """Un vehicule rattache a un client, identifie par sa plaque."""

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="vehicles",
        verbose_name="Client",
    )
    license_plate = models.CharField("Immatriculation", max_length=20, unique=True)
    brand = models.CharField("Marque", max_length=80)
    model = models.CharField("Modele", max_length=80)
    year = models.PositiveIntegerField("Annee", null=True, blank=True)
    vin = models.CharField("Numero de serie (VIN)", max_length=40, blank=True)
    created = models.DateTimeField("Cree le", auto_now_add=True)

    class Meta:
        verbose_name = "Vehicule"
        verbose_name_plural = "Vehicules"
        ordering = ["license_plate"]

    def __str__(self):
        return f"{self.license_plate} — {self.brand} {self.model}"


class Service(models.Model):
    """Un acte du catalogue (remplacement, reparation, supplement...)."""

    class Category(models.TextChoices):
        PARE_BRISE = "pare_brise", "Pare-brise"
        VITRE_LATERALE = "vitre_laterale", "Vitre laterale"
        LUNETTE = "lunette", "Lunette arriere"
        JOINT = "joint", "Joint et etancheite"
        ACCESSOIRE = "accessoire", "Accessoire et piece"
        MAIN_OEUVRE = "main_oeuvre", "Main d'oeuvre"

    code = models.CharField("Code", max_length=40, unique=True)
    name = models.CharField("Designation", max_length=255)
    description = models.TextField("Description", blank=True)
    category = models.CharField(
        "Categorie", max_length=20, choices=Category.choices,
    )
    price = models.DecimalField(
        "Prix HT", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Laisser vide si 'sur devis'.",
    )
    price_on_request = models.BooleanField("Sur devis", default=False)
    is_supplement = models.BooleanField("Supplement", default=False)
    active = models.BooleanField("Actif", default=True)
    created = models.DateTimeField("Cree le", auto_now_add=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["category", "code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Insurer(models.Model):
    """Un assureur partenaire et sa remise eventuelle."""

    class SendFormat(models.TextChoices):
        PORTAIL = "portail", "Portail"
        EMAIL = "email", "Email"
        FAX_OU_EMAIL = "fax_ou_email", "Fax ou email"

    class DiscountScope(models.TextChoices):
        PARE_BRISE_AVANT = "pare_brise_avant", "Pare-brise avant (hors supplements)"
        PARE_BRISE_LUNETTE = "pare_brise_lunette", "Pare-brise et lunette"
        IMPACTS = "impacts", "Reparations d'impact"
        TOUS = "tous", "Tous les actes"
        AUCUN = "aucun", "Aucune remise automatique"

    name = models.CharField("Nom", max_length=120)
    main_contact = models.CharField(
        "Contact principal", max_length=200,
        help_text="Email, ou 'fax:0561234567'.",
    )
    secondary_email = models.EmailField("Email secondaire", blank=True)
    send_format = models.CharField(
        "Format d'envoi", max_length=20, choices=SendFormat.choices,
        default=SendFormat.EMAIL,
    )
    portal_url = models.URLField("URL du portail", blank=True)
    partner_code = models.CharField("Code partenaire", max_length=60, blank=True)
    discount_rate = models.DecimalField(
        "Remise (%)", max_digits=5, decimal_places=2, default=Decimal("0.00"),
    )
    discount_scope = models.CharField(
        "Perimetre de la remise", max_length=20, choices=DiscountScope.choices,
        default=DiscountScope.AUCUN,
    )
    notes = models.TextField("Remarque", blank=True)
    active = models.BooleanField("Actif", default=True)
    created = models.DateTimeField("Cree le", auto_now_add=True)

    class Meta:
        verbose_name = "Assureur"
        verbose_name_plural = "Assureurs"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def applies_to(self, service):
        """Indique si la remise de l'assureur s'applique a ce service.

        Le perimetre est resolu par prefixe de code (deterministe et
        independant du libelle de categorie).
        """
        scope = self.discount_scope
        code = (service.code or "").upper()
        if scope == self.DiscountScope.AUCUN:
            return False
        if scope == self.DiscountScope.TOUS:
            return True
        if scope == self.DiscountScope.PARE_BRISE_AVANT:
            return code.startswith("PB_AVANT") and not service.is_supplement
        if scope == self.DiscountScope.PARE_BRISE_LUNETTE:
            return code.startswith("PB_") or code.startswith("LUN_")
        if scope == self.DiscountScope.IMPACTS:
            return code.startswith("IMPACT")
        return False


class Quote(models.Model):
    """Un devis : un ensemble de services pour un vehicule."""

    class Status(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        ENVOYE = "envoye", "Envoye"
        ACCEPTE = "accepte", "Accepte"
        FACTURE = "facture", "Facture"
        REFUSE = "refuse", "Refuse"

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="quotes",
        verbose_name="Vehicule",
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="quotes",
        verbose_name="Client",
    )
    insurer = models.ForeignKey(
        Insurer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="quotes", verbose_name="Assureur",
    )
    status = models.CharField(
        "Statut", max_length=20, choices=Status.choices, default=Status.BROUILLON,
    )
    discount = models.DecimalField(
        "Remise manuelle (HT)", max_digits=10, decimal_places=2,
        default=Decimal("0.00"),
        help_text="Remise supplementaire saisie a la main (en plus de l'assureur).",
    )
    vat_rate = models.DecimalField(
        "Taux de TVA (%)", max_digits=5, decimal_places=2, default=Decimal("20.00"),
    )
    subtotal_ht = models.DecimalField(
        "Sous-total HT", max_digits=10, decimal_places=2, default=Decimal("0.00"),
    )
    vat_amount = models.DecimalField(
        "Montant TVA", max_digits=10, decimal_places=2, default=Decimal("0.00"),
    )
    total_ttc = models.DecimalField(
        "Total TTC", max_digits=10, decimal_places=2, default=Decimal("0.00"),
    )
    notes = models.TextField("Notes", blank=True)
    created = models.DateTimeField("Cree le", auto_now_add=True)

    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ["-created"]

    def __str__(self):
        return f"Devis #{self.pk} — {self.vehicle.license_plate}"

    def insurer_discount_amount(self, items=None):
        """Montant de la remise assureur, calculee sur les actes du perimetre."""
        if not self.insurer:
            return Decimal("0.00")
        if items is None:
            items = list(self.items.select_related("service"))
        base = sum(
            (it.line_total() for it in items if self.insurer.applies_to(it.service)),
            Decimal("0.00"),
        )
        amount = base * self.insurer.discount_rate / Decimal("100")
        return amount.quantize(CENTS)

    def recalc_total(self):
        """Recalcule sous-total HT, TVA et TTC.

        subtotal_ht = somme des lignes - remise assureur - remise manuelle
        vat_amount  = subtotal_ht * vat_rate / 100
        total_ttc   = subtotal_ht + vat_amount
        A appeler apres chaque ajout/retrait de service.
        """
        items = list(self.items.select_related("service"))
        gross = sum((it.line_total() for it in items), Decimal("0.00"))
        insurer_disc = self.insurer_discount_amount(items)
        total_discount = insurer_disc + (self.discount or Decimal("0.00"))

        self.subtotal_ht = (gross - total_discount).quantize(CENTS)
        self.vat_amount = (self.subtotal_ht * self.vat_rate / Decimal("100")).quantize(CENTS)
        self.total_ttc = (self.subtotal_ht + self.vat_amount).quantize(CENTS)
        return self.total_ttc


class QuoteItem(models.Model):
    """Une ligne de devis : un service, une quantite, un prix fige."""

    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name="items", verbose_name="Devis",
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="quote_items",
        verbose_name="Service",
    )
    quantity = models.PositiveIntegerField("Quantite", default=1)
    unit_price = models.DecimalField(
        "Prix unitaire HT", max_digits=10, decimal_places=2,
    )

    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"

    def __str__(self):
        return f"{self.service.code} x{self.quantity}"

    def line_total(self):
        return (self.unit_price * self.quantity).quantize(CENTS)


class Invoice(models.Model):
    """Une facture issue d'un devis (relation 1-1)."""

    quote = models.OneToOneField(
        Quote, on_delete=models.CASCADE, related_name="invoice", verbose_name="Devis",
    )
    number = models.CharField("Numero", max_length=20, unique=True)
    issued = models.DateField("Date d'emission", auto_now_add=True)
    paid = models.BooleanField("Payee", default=False)
    paid_date = models.DateField("Date de paiement", null=True, blank=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ["-issued", "-number"]

    def __str__(self):
        return self.number


class RepairHistory(models.Model):
    """Historique des interventions (reprises du CSV ou nouvelles)."""

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="repairs",
        verbose_name="Vehicule",
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="repairs",
        verbose_name="Client",
    )
    date = models.DateField("Date")
    intervention_text = models.TextField("Intervention")
    amount_ht = models.DecimalField("Montant HT", max_digits=10, decimal_places=2)
    status_text = models.CharField("Statut", max_length=80, blank=True)
    notes = models.TextField("Notes", blank=True)
    is_legacy = models.BooleanField("Reprise historique", default=False)
    created = models.DateTimeField("Cree le", auto_now_add=True)

    class Meta:
        verbose_name = "Historique d'intervention"
        verbose_name_plural = "Historique des interventions"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} — {self.vehicle.license_plate} — {self.amount_ht} € HT"
