"""Vues d'AtelierVitre.

Toutes les vues exigent une connexion (login_required). Les vues marquees
"provisoire" seront implementees dans les etapes suivantes.
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import utils
from .forms import ClientForm, DateRangeForm, QuoteForm, VehicleForm
from .models import Client, Invoice, Quote, QuoteItem, Service, Vehicle


@login_required
def dashboard(request):
    """Accueil : boutons d'action + facturation de la semaine et du mois."""
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def billed_since(since):
        return Invoice.objects.filter(issued__gte=since).aggregate(
            total=Sum("quote__total_ttc"),
        )["total"] or 0

    context = {
        "week_total": billed_since(week_start),
        "month_total": billed_since(month_start),
    }
    return render(request, "core/dashboard.html", context)


# --- Devis ---

@login_required
def quote_create(request):
    """Nouveau devis : plaque existante (reutilisee) ou nouvelle (creee)."""
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                vehicle = form.existing_vehicle
                if vehicle is None:
                    client, _ = Client.objects.get_or_create(
                        name=data["client_name"].strip(),
                        defaults={
                            "email": data.get("client_email", ""),
                            "phone": data.get("client_phone", ""),
                        },
                    )
                    vehicle = Vehicle.objects.create(
                        client=client,
                        license_plate=data["license_plate"].strip(),
                        brand=data["brand"].strip(),
                        model=data["model"].strip(),
                        year=data.get("year"),
                    )
                else:
                    client = vehicle.client

                quote = Quote.objects.create(
                    client=client,
                    vehicle=vehicle,
                    insurer=data.get("insurer"),
                    discount=data.get("discount") or 0,
                    notes=data.get("notes", ""),
                )
                for service in data["services"]:
                    QuoteItem.objects.create(
                        quote=quote, service=service,
                        unit_price=service.price, quantity=1,
                    )
                quote.recalc_total()
                quote.save()

            messages.success(request, f"Devis n° {quote.id} cree.")
            return redirect("quote_detail", pk=quote.pk)
    else:
        form = QuoteForm(initial={"license_plate": request.GET.get("plate", "")})

    # Services groupes par categorie pour un affichage lisible.
    groups = {}
    for service in (
        Service.objects.filter(active=True, price_on_request=False)
        .order_by("category", "name")
    ):
        groups.setdefault(service.get_category_display(), []).append(service)
    selected = {int(pk) for pk in request.POST.getlist("services")}

    context = {
        "form": form,
        "service_groups": groups,
        "selected_services": selected,
    }
    return render(request, "core/quote_form.html", context)


@login_required
def quote_detail(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related("client", "vehicle", "insurer"), pk=pk,
    )
    invoice = Invoice.objects.filter(quote=quote).first()
    context = {
        "quote": quote,
        "items": quote.items.select_related("service"),
        "insurer_discount": quote.insurer_discount_amount(),
        "invoice": invoice,
    }
    return render(request, "core/quote_detail.html", context)


@login_required
def quote_pdf(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    pdf = utils.quote_pdf_bytes(quote)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="devis_{quote.id}.pdf"'
    return response


@login_required
def quote_email(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    if request.method != "POST":
        return redirect("quote_detail", pk=pk)
    if not quote.client.email:
        messages.error(request, "Ce client n'a pas d'adresse email.")
        return redirect("quote_detail", pk=pk)

    email = EmailMessage(
        subject=f"Devis AtelierVitre n° {quote.id}",
        body=(
            "Bonjour,\n\nVeuillez trouver ci-joint votre devis.\n\n"
            "Cordialement,\nAtelierVitre"
        ),
        to=[quote.client.email],
    )
    email.attach(f"devis_{quote.id}.pdf", utils.quote_pdf_bytes(quote), "application/pdf")
    email.send()
    messages.success(request, f"Devis envoye a {quote.client.email}.")
    return redirect("quote_detail", pk=pk)


@login_required
def quote_to_invoice(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    if request.method != "POST":
        return redirect("quote_detail", pk=pk)
    invoice = utils.create_invoice_for_quote(quote)
    messages.success(request, f"Facture {invoice.number} creee.")
    return redirect("quote_detail", pk=pk)


# --- Factures ---

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    pdf = utils.invoice_pdf_bytes(invoice)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.number}.pdf"'
    return response


@login_required
def invoice_email(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method != "POST":
        return redirect("quote_detail", pk=invoice.quote_id)
    client = invoice.quote.client
    if not client.email:
        messages.error(request, "Ce client n'a pas d'adresse email.")
        return redirect("quote_detail", pk=invoice.quote_id)

    email = EmailMessage(
        subject=f"Facture AtelierVitre {invoice.number}",
        body=(
            "Bonjour,\n\nVeuillez trouver ci-joint votre facture.\n\n"
            "Cordialement,\nAtelierVitre"
        ),
        to=[client.email],
    )
    email.attach(f"{invoice.number}.pdf", utils.invoice_pdf_bytes(invoice), "application/pdf")
    email.send()
    messages.success(request, f"Facture envoyee a {client.email}.")
    return redirect("quote_detail", pk=invoice.quote_id)


# --- Vues provisoires (implementees aux etapes suivantes) ---

@login_required
def client_create(request):
    """Alta client + vehicule dans un seul formulaire -> fiche client."""
    if request.method == "POST":
        client_form = ClientForm(request.POST)
        vehicle_form = VehicleForm(request.POST)
        if client_form.is_valid() and vehicle_form.is_valid():
            with transaction.atomic():
                client = client_form.save()
                vehicle = vehicle_form.save(commit=False)
                vehicle.client = client
                vehicle.save()
            messages.success(request, f"Client « {client.name} » cree.")
            return redirect("client_detail", pk=client.pk)
    else:
        client_form = ClientForm()
        vehicle_form = VehicleForm()

    return render(request, "core/client_form.html", {
        "client_form": client_form,
        "vehicle_form": vehicle_form,
    })


@login_required
def client_detail(request, pk):
    """Fiche client : coordonnees, vehicules et historique complet."""
    client = get_object_or_404(Client, pk=pk)
    context = {
        "client": client,
        "vehicles": client.vehicles.all(),
        "repairs": client.repairs.select_related("vehicle"),
        "quotes": client.quotes.select_related("vehicle"),
        "invoices": Invoice.objects.filter(quote__client=client).select_related("quote"),
    }
    return render(request, "core/client_detail.html", context)


@login_required
def search(request):
    """Recherche par nom de client ou immatriculation -> liste de fiches."""
    query = (request.GET.get("q") or "").strip()
    clients = []
    if query:
        clients = (
            Client.objects.filter(
                Q(name__icontains=query)
                | Q(vehicles__license_plate__icontains=query)
            )
            .distinct()
            .prefetch_related("vehicles")
        )
    return render(request, "core/search.html", {"query": query, "clients": clients})


@login_required
def search_json(request):
    """Endpoint JSON pour l'autocompletion (par plaque ou nom)."""
    query = (request.GET.get("q") or "").strip()
    results = []
    if query:
        vehicles = (
            Vehicle.objects.filter(
                Q(license_plate__icontains=query)
                | Q(client__name__icontains=query)
            )
            .select_related("client")[:10]
        )
        for v in vehicles:
            results.append({
                "plate": v.license_plate,
                "brand": v.brand,
                "model": v.model,
                "year": v.year,
                "client_id": v.client_id,
                "client_name": v.client.name,
                "client_email": v.client.email,
                "client_phone": v.client.phone,
            })
    return JsonResponse({"results": results})


def _filtered_invoices(request):
    """Factures filtrees par periode (parametres GET date_from / date_to)."""
    form = DateRangeForm(request.GET or None)
    invoices = (
        Invoice.objects
        .select_related("quote", "quote__client")
        .order_by("issued", "number")
    )
    date_from = date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        if date_from:
            invoices = invoices.filter(issued__gte=date_from)
        if date_to:
            invoices = invoices.filter(issued__lte=date_to)
    return form, invoices, date_from, date_to


@login_required
def report(request):
    """Rapport des ventes : factures d'une periode + totaux HT/TVA/TTC."""
    form, invoices, date_from, date_to = _filtered_invoices(request)
    totals = invoices.aggregate(
        ht=Sum("quote__subtotal_ht"),
        tva=Sum("quote__vat_amount"),
        ttc=Sum("quote__total_ttc"),
    )
    context = {
        "form": form,
        "invoices": invoices,
        "totals": totals,
        "query": request.GET.urlencode(),
    }
    return render(request, "core/report.html", context)


@login_required
def report_excel(request):
    """Export Excel du rapport des ventes (openpyxl)."""
    from openpyxl import Workbook

    _, invoices, _, _ = _filtered_invoices(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventes"
    ws.append(["Numero", "Date", "Client", "HT", "TVA", "TTC"])

    total_ht = total_tva = total_ttc = 0
    for inv in invoices:
        q = inv.quote
        ws.append([
            inv.number,
            inv.issued.strftime("%d/%m/%Y"),
            q.client.name,
            float(q.subtotal_ht),
            float(q.vat_amount),
            float(q.total_ttc),
        ])
        total_ht += q.subtotal_ht
        total_tva += q.vat_amount
        total_ttc += q.total_ttc

    ws.append(["Total", "", "", float(total_ht), float(total_tva), float(total_ttc)])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="rapport_ventes.xlsx"'
    wb.save(response)
    return response
