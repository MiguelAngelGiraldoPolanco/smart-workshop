# Projet — Test technique Koralya

Bienvenue ! Tu travailles sur un serveur préinstallé pour ton test technique.
**Tu n'as PAS besoin de sudo** pour rien : tout est déjà configuré.

---

## 🚀 Lancer le projet

Le serveur **gunicorn** tourne déjà en tâche de fond avec `--reload` activé.

```
http://178.104.96.220/
```

Quand tu modifies un fichier `.py`, gunicorn redémarre automatiquement.
Rafraîchis le navigateur et tu vois tes changements.

---

## 🐘 Base de données PostgreSQL

PostgreSQL 16 déjà connectée au projet Django (déjà configurée dans
`projet/settings.py`) :

| Paramètre | Valeur      |
|-----------|-------------|
| Host      | `127.0.0.1` |
| Port      | `5432`      |
| Database  | `candidato` |
| User      | `candidato` |
| Password  | `candidato` |

Pour ouvrir un shell SQL :

```bash
psql -h 127.0.0.1 -U candidato -d candidato
# password : candidato
```

Tu peux créer d'autres bases (`createdb mabase`).

---

## 🔴 Redis

Déjà installé et démarré sur `127.0.0.1:6379` (pour Celery, cache, sessions).

```bash
redis-cli
```

---

## 📦 Paquets Python disponibles (`~/base_venv/`)

```bash
source ~/base_venv/bin/activate
```

Déjà installés :

- **Web** : Django 6, djangorestframework, gunicorn, whitenoise, django-cors-headers
- **HTTP** : requests, httpx
- **PDF** : weasyprint (testé)
- **Image** : Pillow
- **Scraping** : beautifulsoup4, lxml
- **Async/Tâches** : celery + redis (client)
- **DB** : psycopg2-binary
- **Données/Excel** : pandas, openpyxl
- **Tests** : pytest, pytest-django
- **Config** : python-dotenv, django-environ

Tu peux installer ce que tu veux avec `pip install <paquet>`.

---

## 🤖 Claude Code (déjà authentifié)

Le CLI **Claude Code** (Opus 4.7) est installé avec notre compte Anthropic.
**Pas besoin de compte Claude.**

```bash
claude
```

L'extension VS Code **Claude Code** est aussi pré-installée. Dans VS Code :
`Ctrl+Shift+P` → "Claude".

> 💡 Tu peux écrire à Claude en **espagnol**. Lui programmera le projet en
> **français** (interface, textes utilisateur). C'est exactement comme on
> travaille en interne chez Koralya.

---

## 📁 Structure du projet

```
~/proyecto/
├── manage.py
├── projet/
│   ├── settings.py    ← DATABASES déjà configuré sur postgres
│   ├── urls.py
│   └── wsgi.py
├── README.md          ← ce fichier
└── CLAUDE.md          ← contexte pour Claude Code
```

---

## 🌐 Accès au site

| URL                              | Quoi |
|----------------------------------|------|
| `http://178.104.96.220/`         | Ton site Django |
| `http://178.104.96.220/admin/`   | Admin Django (`python manage.py createsuperuser`) |

---

## 🔧 Détails techniques

- **OS** : Ubuntu 24.04 LTS
- **Python** : 3.12.3 (`~/base_venv/`)
- **Node.js** : v20.20.2
- **Stack** : nginx → gunicorn (`--reload`, port 8000) → Django
- **Static** : `staticfiles/` servi par nginx (`/static/`)
- **Media** : `media/` servi par nginx (`/media/`)

---

Bonne chance ! 🍀

— L'équipe Koralya


## Acceso a la aplicación

Usuario de prueba (superusuario):
- Usuario: root
- Contraseña: password

Para crear el usuario en una instalación limpia:
    python manage.py createsuperuser

Acceso al panel de administración de Django: /admin
Acceso a la aplicación: /

> Nota: estas son credenciales de prueba para facilitar la evaluación.
> En un entorno real, los usuarios se crearían de forma segura y nunca
> se documentarían credenciales en texto plano en el repositorio.