# Contexte du projet pour Claude Code

Ce fichier décrit l'environnement. Lis-le avant de proposer des commandes ou
des installations.

## Environnement
- **OS** : Ubuntu 24.04 LTS, **pas de sudo disponible** pour le candidat
- **Python** : 3.12.3 dans le venv `~/base_venv/`
- **Node** : v20
- **Stack web** : nginx (port 80) → gunicorn (`--reload`, port 8000) → Django

## Base de données
PostgreSQL 16 **déjà configurée** dans `projet/settings.py` :
- DATABASES.default → `postgresql://candidato:candidato@127.0.0.1:5432/candidato`
- N'invente pas la connexion : c'est déjà fait
- Pour ouvrir psql : `psql -h 127.0.0.1 -U candidato -d candidato` (password `candidato`)

## Redis
Disponible sur `127.0.0.1:6379` pour Celery/cache.

## Paquets Python pré-installés (n'installe rien si tu vois déjà le paquet)
Django 6.0, DRF, gunicorn, weasyprint (PDF), Pillow, requests, httpx,
beautifulsoup4, lxml, celery, redis, psycopg2-binary, pandas, openpyxl,
pytest, pytest-django, python-dotenv, django-environ, whitenoise,
django-cors-headers.

## Auto-reload
Le service `proyecto-gunicorn` se relance automatiquement quand un fichier
`.py` change. **Ne lance pas `python manage.py runserver`** — gunicorn s'en charge.

Pour appliquer une migration :
```bash
cd ~/proyecto && python manage.py migrate
```

Si vraiment besoin de redémarrer gunicorn, ce n'est pas accessible sans sudo.

## Tests
`pytest` + `pytest-django` disponibles. Lance avec `pytest`.

## Static / media
- `python manage.py collectstatic` → `~/proyecto/staticfiles/`
- nginx les sert depuis `/static/` et `/media/`

## Langue du projet
- Le **produit final doit être en français** (UI, messages utilisateur).
- Le candidat te parle en **espagnol** ; toi tu programmes en français.
- Settings : `LANGUAGE_CODE = "fr-fr"`, `TIME_ZONE = "Europe/Paris"`.

## URL d'accès du site
`http://178.104.96.220/` (firewall ouvert uniquement à l'IP du candidat
en cours).

## Limites
- Pas de sudo
- Le serveur est éphémère : il sera détruit après le test
- Tout ce qui est dans `~/proyecto/` sera sauvegardé automatiquement quand
  le candidat clique "Terminer entrevista"
