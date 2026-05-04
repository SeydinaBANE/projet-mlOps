# CLAUDE.md

Ce fichier fournit des instructions à Claude Code (claude.ai/code) pour travailler dans ce dépôt.

## Vue d'ensemble

Pipeline MLOps e-commerce composé de trois composants : un dashboard Dash temps réel, une API REST FastAPI, et un modèle de prédiction de churn scikit-learn. Tous alimentés par PostgreSQL.

## Configuration initiale

Copier `.env.example` vers `.env` et ajuster les valeurs si nécessaire :
```bash
cp .env.example .env
```

Les trois variables obligatoires sont `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Toutes les connexions DB lisent ces variables via `python-dotenv` — ne jamais hardcoder de credentials.

## Prérequis — Base de données

Lancer PostgreSQL avec Docker Compose (schéma créé automatiquement) :
```bash
docker compose up -d
```

Ou manuellement (sans initialisation automatique du schéma) :
```bash
docker run --name postgres-ecom \
  -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin123 -e POSTGRES_DB=ecommerce \
  -p 5432:5432 -d postgres:15
```

## Commandes

**Installer les dépendances** :
```bash
uv sync
# Avec dépendances de développement (pytest) :
uv sync --extra dev
```

**Dashboard** (Dash, port 8050) :
```bash
uv run python dashboard/app.py
```

**API** (FastAPI, port 8000) — depuis la racine du projet :
```bash
uvicorn dashboard.api.main:app --reload --port 8000
```

**Entraîner le modèle de churn** (lit la DB, écrit `ml/churn_model.pkl`) :
```bash
uv run python ml/churn_model.py
```

**Lancer les tests** :
```bash
uv run pytest
# Un seul fichier :
uv run pytest tests/test_ml.py -v
```

## Architecture

```
projet-mlOps/
├── dashboard/
│   ├── app.py          # App Dash — rafraîchissement toutes les 10s via dcc.Interval
│   └── api/
│       └── main.py     # FastAPI — /ventes, /clients, /produits, /kpis, /churn
├── ml/
│   ├── churn_model.py  # Entraînement RandomForestClassifier, sauvegarde pkl
│   └── churn_model.pkl # Artefact du modèle (généré, ignoré par git)
├── tests/
│   ├── test_api.py     # Tests FastAPI avec TestClient + mocks DB
│   └── test_ml.py      # Tests unitaires preparer_features() et entrainer_modele()
├── schema.sql          # Schéma SQL (monté automatiquement par docker-compose)
├── docker-compose.yml  # PostgreSQL + initialisation automatique du schéma
└── .env.example        # Template des variables d'environnement
```

**Flux de données :**
- `dashboard/app.py` et `dashboard/api/main.py` interrogent PostgreSQL directement via `psycopg2`.
- `ml/churn_model.py` utilise SQLAlchemy pour lire les features clients/commandes, entraîne un RandomForest et sérialise le modèle.
- L'endpoint `/churn` de l'API charge le pkl et retourne les prédictions par client.

**Schéma DB :** `customers` (id, nom, pays), `products` (id, nom, prix), `orders` (id, customer_id, statut, montant_total, created_at), `order_items` (id, order_id, product_id, quantite, prix_unitaire).

**Variable `CHURN_JOURS_INACTIF`** (défaut : 30) : seuil en jours d'inactivité au-delà duquel un client est labellisé churn.

**Note :** L'API doit être lancée depuis la racine du projet (`uvicorn dashboard.api.main:app`) pour que le chemin `ml/churn_model.pkl` soit résolu correctement.
