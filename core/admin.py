"""Configuration de l'admin Django pour AtelierVitre."""
from django.contrib import admin

from .models import (
    Client,
    Insurer,
    Invoice,
    Quote,
    QuoteItem,
    RepairHistory,
    Service,
    Vehicle,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("license_plate", "brand", "model", "year", "client")
    search_fields = ("license_plate", "brand", "model", "client__name")
    list_select_related = ("client",)
    ordering = ("license_plate",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "code", "name", "category", "price",
        "price_on_request", "is_supplement", "active",
    )
    list_filter = ("category", "active", "is_supplement", "price_on_request")
    search_fields = ("code", "name")
    ordering = ("category", "code")


@admin.register(Insurer)
class InsurerAdmin(admin.ModelAdmin):
    list_display = (
        "name", "send_format", "discount_rate", "discount_scope", "active",
    )
    list_filter = ("send_format", "active", "discount_scope")
    search_fields = ("name", "main_contact")


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    autocomplete_fields = ("service",)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "id", "vehicle", "client", "status", "insurer", "total_ttc", "created",
    )
    list_filter = ("status", "insurer")
    search_fields = ("vehicle__license_plate", "client__name")
    list_select_related = ("vehicle", "client", "insurer")
    autocomplete_fields = ("vehicle", "client", "insurer")
    inlines = (QuoteItemInline,)
    readonly_fields = ("subtotal_ht", "vat_amount", "total_ttc")

    def save_related(self, request, form, formsets, change):
        """Recalcule les totaux apres l'enregistrement des lignes."""
        super().save_related(request, form, formsets, change)
        quote = form.instance
        quote.recalc_total()
        quote.save(update_fields=["subtotal_ht", "vat_amount", "total_ttc"])


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "quote", "issued", "paid", "paid_date")
    list_filter = ("paid",)
    search_fields = ("number", "quote__client__name")
    list_select_related = ("quote",)


@admin.register(RepairHistory)
class RepairHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "date", "vehicle", "client", "amount_ht", "status_text", "is_legacy",
    )
    list_filter = ("is_legacy", "status_text")
    search_fields = ("vehicle__license_plate", "client__name", "intervention_text")
    list_select_related = ("vehicle", "client")
    date_hierarchy = "date"
