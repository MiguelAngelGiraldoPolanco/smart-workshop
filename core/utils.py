"""Utilitaires : generation PDF (WeasyPrint) et numerotation des factures."""
from decimal import Decimal

from django.db import transaction
from django.template.loader import render_to_string
from weasyprint import HTML

# Donnees fiscales du vendeur (AtelierVitre) — figurent sur les factures.
SELLER = {
    "name": "AtelierVitre — Pascal Fournier",
    "address": "12 rue des Mecaniciens, 31000 Toulouse",
    "siret": "538 247 192 00018",
    "vat": "FR45538247192",
    "email": "contact@ateliervitre.fr",
}


def render_pdf(template_name, context):
    """Rend un template HTML en PDF (bytes) via WeasyPrint."""
    html = render_to_string(template_name, context)
    return HTML(string=html).write_pdf()


def _quote_context(quote):
    """Contexte commun aux PDF devis et facture (lignes + ventilation)."""
    items = list(quote.items.select_related("service"))
    gross = sum((it.line_total() for it in items), Decimal("0.00"))
    return {
        "quote": quote,
        "items": items,
        "seller": SELLER,
        "gross": gross,
        "insurer_discount": quote.insurer_discount_amount(items),
        "manual_discount": quote.discount or Decimal("0.00"),
    }


def quote_pdf_bytes(quote):
    """PDF d'un devis."""
    return render_pdf("core/quote_pdf.html", _quote_context(quote))


def invoice_pdf_bytes(invoice):
    """PDF d'une facture (meme ventilation que le devis + entete facture)."""
    context = _quote_context(invoice.quote)
    context["invoice"] = invoice
    return render_pdf("core/invoice_pdf.html", context)


def create_invoice_for_quote(quote):
    """Cree la facture d'un devis avec un numero FAC-xxxxx unique.

    Verrouille la derniere facture (select_for_update) dans une transaction
    pour eviter les numeros en double. Idempotent : si la facture existe
    deja, elle est renvoyee telle quelle.
    """
    from .models import Invoice, Quote

    with transaction.atomic():
        existing = Invoice.objects.filter(quote=quote).first()
        if existing:
            return existing

        last = Invoice.objects.select_for_update().order_by("-number").first()
        next_n = (int(last.number.split("-")[1]) + 1) if last else 1
        number = f"FAC-{next_n:05d}"

        invoice = Invoice.objects.create(quote=quote, number=number)
        if quote.status != Quote.Status.FACTURE:
            quote.status = Quote.Status.FACTURE
            quote.save(update_fields=["status"])
        return invoice
