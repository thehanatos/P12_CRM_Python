# 📊 CRM Python CLI

Ce projet est un outil CRM en ligne de commande permettant de gérer des utilisateurs, clients, contrats et événements. Il utilise Python, SQLAlchemy pour la base de données, Click pour l'interface CLI, Questionary pour les menus interactifs, et Sentry pour la journalisation des erreurs.

---

## 🚀 Fonctionnalités

* Authentification avec rôles (`gestion`, `support`, etc.)
* Gestion des clients, des contrats, des événements et des utilisateurs
* Journalisation des erreurs avec Sentry
* Menus interactifs (navigables par flèches)
* Logs et traçabilité d’actions sensibles
* Suivi des contrats et des événèments

---

## 🧰 Technologies utilisées

* Python 3.10+
* SQLAlchemy
* Click
* Questionary
* Sentry SDK
* PostgreSQL
* Alembic (migrations)
* dotenv

---

## ⚙️ Installation

```bash
git clone https://github.com/votre-utilisateur/votre-projet.git
cd votre-projet
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Créer un fichier `.env` à la racine avec :

```
DATABASE_URL=postgresql://user:password@localhost:5432/nom_de_la_base
SENTRY_DSN=https://<public_key>@sentry.io/<project_id>
DB_NAME=<nom_base>
DB_USER=<utilisateur>
DB_PASSWORD=<password>
DB_HOST=localhost
DB_PORT=5432

JWT_SECRET=<cle_secrete>
JWT_ALGO=HS256
JWT_EXPIRATION_MINUTES=60

SENTRY_DSN=<"dsn_sentry">
```

---

## ▶️ Utilisation

```bash
python main.py
```

Choisissez ensuite une catégorie à gérer via le menu (Utilisateurs, Événements, etc.).

---

## 🧪 Tests

Tests unitaires (exemple avec `pytest` et `coverage`) :

```bash
pytest --cov=crm
```

---

## 📋 Journalisation avec Sentry

* Toutes les erreurs inattendues sont capturées avec `sentry_sdk.capture_exception(e)`
* Les actions critiques sont journalisées avec `sentry_sdk.capture_message(...)` :
  * Création / modification d’utilisateur
  * Signature de contrat

Exemple dans le code :

```python
try:
    # action
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

---

## ✨ Exemple de menu CLI

```bash
$ python main.py

Que voulez-vous gérer ?
> Utilisateurs
  Clients
  Contrats
  Événements
  Admin
  Quitter
```

---

## 📂 Arborescence simplifiée

```
.
├── crm/
│   ├── cli.py
│   ├── models.py
│   ├── auth.py
|   ├── database.py
├── tests/
├── flake8-report/
├── migrations/
├── main.py
├── .env
├── .token
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## 📄 Licence

Ce projet est sous licence MIT.
