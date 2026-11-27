# AtelierVitre — Deploiement et mise en route

Application Django (monolithe, app `core`) de gestion de reparations de
vitrage auto : devis, factures PDF, historique clients, rapport des ventes.

## 1. Prerequis (deja en place sur le serveur de test)

- Python 3.12 dans `~/base_venv/` (`source ~/base_venv/bin/activate`)
- PostgreSQL 16, Redis, nginx -> gunicorn (`--reload`, port 8000)
- Dependances : `pip install -r requirements.txt`
- Configuration sensible dans `.env` (voir `.env.example`)

## 2. Mise en route (ordre exact)

```bash
cd ~/proyecto
source ~/base_venv/bin/activate

# 1. Schema de base de donnees
python manage.py migrate

# 2. Donnees : catalogue, assureurs, historique des reparations
python manage.py import_catalog       # 43 services (PDF cure)
python manage.py import_insurers      # 3 assureurs (assureurs.json)
python manage.py import_reparations   # 16 clients / 16 vehicules / 20 interventions

# 3. Superutilisateur (root / password)
python manage.py create_admin

# 4. Fichiers statiques (servis par nginx depuis /static/)
python manage.py collectstatic --noinput
```

> Pas de `runserver` : gunicorn tourne deja avec `--reload` et redemarre
> automatiquement a chaque modification d'un `.py`.

Acces : http://178.104.96.220/ — admin Django : http://178.104.96.220/admin/

## 3. Note sur les fichiers statiques (nginx 403)

Sur ce serveur de test, nginx (`www-data`) sert les statiques via
`location /static/ -> alias .../staticfiles/`, mais `/home/candidato` avait
les permissions `drwxr-x---` qui empechaient `www-data` de **traverser** le
dossier, provoquant un **403** sur `/static/...`. Resolu par :

```bash
chmod o+x /home/candidato      # traversee seule (pas de listage)
```

Dans un deploiement propre, l'application ne vivrait pas sous `/home` d'un
utilisateur : le code serait sous `/srv/ateliervitre` (ou `/var/www`) avec un
groupe partage avec `www-data`, ce qui evite ce contournement.

## 4. Checklist de test manuel

1. **Connexion** : `/login/` avec `root` / `password` -> tableau de bord.
2. **Tableau de bord** : 4 gros boutons + facturation semaine / mois.
3. **Nouveau client** : creer client + vehicule -> redirige vers la fiche.
4. **Recherche** : par nom (`Dupont`) ou plaque (`AB-432-CD`) -> fiche avec
   vehicules + historique (reprises du CSV).
5. **Nouveau devis** : saisir une plaque existante (autocompletion) ou une
   nouvelle ; cocher des services ; choisir un assureur (remise auto) ->
   totaux HT / TVA 20% / TTC.
6. **PDF / email** : « Telecharger le PDF » et « Envoyer par email »
   (backend console : le mail s'affiche dans les logs gunicorn).
7. **Facturer** : « Convertir en facture » -> numero `FAC-00001`, statut
   `facture`.
8. **Rapport** : filtrer par dates -> liste + total HT/TVA/TTC + export Excel.
