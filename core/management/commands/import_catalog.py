"""Importe le catalogue des tarifs (catalogue_tarifs.pdf) dans Service.

Le catalogue est un actif fige : la liste est curee a partir du PDF
(robuste et idempotente). Les actes sans code dans le PDF (joints, main
d'oeuvre) recoivent un code synthetique. Idempotent via update_or_create
sur 'code'.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Service

C = Service.Category

# (code, name, category, price, price_on_request, is_supplement, description)
CATALOG = [
    # --- 1. Pare-brise ---
    ("PB_AVANT_STD", "Remplacement pare-brise avant — vehicule standard", C.PARE_BRISE, "250.00", False, False, "Citadines, berlines."),
    ("PB_AVANT_PREM", "Remplacement pare-brise avant — premium", C.PARE_BRISE, "390.00", False, False, "BMW, Audi, Mercedes serie C+."),
    ("PB_AVANT_4X4", "Remplacement pare-brise avant — SUV / 4x4", C.PARE_BRISE, "320.00", False, False, ""),
    ("PB_AVANT_UTIL", "Remplacement pare-brise avant — utilitaire", C.PARE_BRISE, "280.00", False, False, "Kangoo, Berlingo, Trafic, Master."),
    ("PB_AVANT_PL", "Remplacement pare-brise avant — poids lourd / camion", C.PARE_BRISE, None, True, False, ""),
    ("PB_TEINTE", "Supplement pare-brise teinte", C.PARE_BRISE, "45.00", False, True, ""),
    ("PB_CHAUFFANT", "Supplement pare-brise chauffant (technologie atherm)", C.PARE_BRISE, "80.00", False, True, ""),
    ("PB_ADAS", "Recalibrage camera ADAS post-remplacement", C.PARE_BRISE, "95.00", False, False, "Obligatoire vehicules recents."),
    ("IMPACT_RES", "Reparation impact (resine) — 1 impact", C.PARE_BRISE, "80.00", False, False, ""),
    ("IMPACT_2", "Reparation impact — 2e impact sur meme intervention", C.PARE_BRISE, "40.00", False, True, ""),
    ("IMPACT_FISSURE", "Reparation fissure jusqu'a 25 cm (resine)", C.PARE_BRISE, "110.00", False, False, "A partir de 110,00 EUR HT."),
    ("JOINT_PB", "Changement joint pare-brise seul (sans changement vitre)", C.JOINT, "120.00", False, False, ""),

    # --- 2. Vitres laterales ---
    ("VL_AV_GA", "Vitre avant gauche (conducteur) — standard", C.VITRE_LATERALE, "180.00", False, False, ""),
    ("VL_AV_DR", "Vitre avant droite (passager) — standard", C.VITRE_LATERALE, "180.00", False, False, ""),
    ("VL_AR_GA", "Vitre arriere gauche", C.VITRE_LATERALE, "160.00", False, False, ""),
    ("VL_AR_DR", "Vitre arriere droite", C.VITRE_LATERALE, "160.00", False, False, ""),
    ("VL_PREM", "Supplement vitre laterale premium (BMW, Audi...)", C.VITRE_LATERALE, "60.00", False, True, ""),
    ("VL_TEINTE", "Supplement vitre teintee d'origine", C.VITRE_LATERALE, "35.00", False, True, ""),
    ("VL_LECH", "Changement leche-vitre (par cote, interieur ou exterieur)", C.VITRE_LATERALE, "45.00", False, False, "Par cote / par piece."),
    ("VL_REGUL", "Reparation mecanisme leve-vitre (hors pieces)", C.VITRE_LATERALE, None, True, False, "Main d'oeuvre, voir tarif horaire."),

    # --- 3. Lunette arriere ---
    ("LUN_STD", "Lunette arriere — vehicule standard", C.LUNETTE, "220.00", False, False, ""),
    ("LUN_DEGIV", "Lunette arriere avec degivrage", C.LUNETTE, "270.00", False, False, ""),
    ("LUN_HAYON", "Lunette de hayon (break / SUV)", C.LUNETTE, "280.00", False, False, ""),
    ("LUN_TEINTE", "Supplement lunette teintee", C.LUNETTE, "40.00", False, True, ""),
    ("LUN_ANT_RAD", "Supplement antenne radio integree", C.LUNETTE, "30.00", False, True, ""),
    ("LUN_PL", "Lunette poids lourd / camion", C.LUNETTE, None, True, False, ""),

    # --- 4. Joints et etancheite (codes synthetiques) ---
    ("JOINT_PORTIERE", "Joint de portiere avant ou arriere", C.JOINT, "65.00", False, False, "Par portiere."),
    ("JOINT_COFFRE", "Joint de coffre / hayon", C.JOINT, "80.00", False, False, ""),
    ("JOINT_CUSTODE", "Joint de vitre custode (vitre fixe arriere des berlines)", C.JOINT, "55.00", False, False, ""),
    ("JOINT_GARNITURE", "Garniture etancheite hayon (kit complet)", C.JOINT, "110.00", False, False, ""),
    ("DIAG_FUITE", "Diagnostic fuite avec test a l'eau", C.JOINT, "35.00", False, False, "Deduit si reparation effectuee."),
    ("JOINT_CUSTOM", "Joint custom (sur mesure vehicule ancien / collection)", C.JOINT, None, True, False, ""),

    # --- 5. Accessoires et pieces ---
    ("ESS_STD", "Essuie-glaces standard (la paire)", C.ACCESSOIRE, "28.00", False, False, ""),
    ("ESS_PREM", "Essuie-glaces premium (Bosch Aerotwin)", C.ACCESSOIRE, "45.00", False, False, ""),
    ("RETROVISEUR", "Retroviseur exterieur — selon modele", C.ACCESSOIRE, "85.00", False, False, "A partir de 85,00 EUR HT."),
    ("RETRO_INT", "Retroviseur interieur", C.ACCESSOIRE, "35.00", False, False, ""),
    ("FILM_TEINTE", "Pose film teinte (par vitre)", C.ACCESSOIRE, None, True, False, "Selon vehicule."),
    ("FILM_TEINTE_KIT", "Pose film teinte kit complet (4 vitres + lunette)", C.ACCESSOIRE, "280.00", False, False, "A partir de 280,00 EUR HT."),
    ("ANTI_PLUIE", "Traitement anti-pluie pare-brise", C.ACCESSOIRE, "25.00", False, False, ""),
    ("ADHESIF", "Adhesif structurel (par cartouche)", C.ACCESSOIRE, "18.00", False, False, ""),
    ("NETT_PROF", "Nettoyage professionnel pare-brise", C.ACCESSOIRE, "15.00", False, False, "Encrassement resine, traces."),
    ("HOMOLOG", "Certificat d'homologation pose film teinte", C.ACCESSOIRE, "12.00", False, False, "Reglementation."),

    # --- 6. Main d'oeuvre ---
    ("MO_HORAIRE", "Main d'oeuvre standard (tarif horaire)", C.MAIN_OEUVRE, "65.00", False, False,
     "65,00 EUR HT/h. Majorations : +15% vehicule ancien (74,75), collection 85,00, "
     "urgence J+0/J+1 +25%, deplacement 0,80 EUR/km au-dela de 15 km."),
]


class Command(BaseCommand):
    help = "Importe le catalogue des tarifs (Service) depuis la liste curee du PDF."

    def handle(self, *args, **options):
        created = updated = 0
        for code, name, category, price, por, supp, desc in CATALOG:
            _, was_created = Service.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "category": category,
                    "price": Decimal(price) if price is not None else None,
                    "price_on_request": por,
                    "is_supplement": supp,
                    "description": desc,
                    "active": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(
            f"Catalogue importe : {created} crees, {updated} mis a jour "
            f"({Service.objects.count()} services au total)."
        ))
