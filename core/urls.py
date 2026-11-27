"""Routes de l'application core.

Monolithe a une seule app : pas de namespace, les noms de routes restent
globaux (ex. 'dashboard', 'login') et coherents avec LOGIN_URL/REDIRECT.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    # Authentification.
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="core/login.html", authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Application.
    path("", views.dashboard, name="dashboard"),
    path("clients/nouveau/", views.client_create, name="client_create"),
    path("clients/<int:pk>/", views.client_detail, name="client_detail"),
    path("recherche/", views.search, name="search"),
    path("recherche/json/", views.search_json, name="search_json"),

    # Devis.
    path("devis/nouveau/", views.quote_create, name="quote_create"),
    path("devis/<int:pk>/", views.quote_detail, name="quote_detail"),
    path("devis/<int:pk>/pdf/", views.quote_pdf, name="quote_pdf"),
    path("devis/<int:pk>/email/", views.quote_email, name="quote_email"),
    path("devis/<int:pk>/facturer/", views.quote_to_invoice, name="quote_to_invoice"),

    # Factures.
    path("factures/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("factures/<int:pk>/email/", views.invoice_email, name="invoice_email"),

    path("rapport/", views.report, name="report"),
    path("rapport/excel/", views.report_excel, name="report_excel"),
]
