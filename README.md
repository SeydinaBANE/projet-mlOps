# E-commerce MLOps Pipeline

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Airflow-2.8-017CEE?style=flat-square&logo=apacheairflow&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![Plotly Dash](https://img.shields.io/badge/Dash-Dashboard-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

Pipeline de données et ML complet simulant un système e-commerce réel.

## Architecture
Sources → PostgreSQL → Airflow → Dash Dashboard
↓
Scikit-learn (Churn)
↓
FastAPI (REST API)

## Stack technique
| Outil | Rôle |
|-------|------|
| Docker | Conteneurisation |
| PostgreSQL | Stockage des données |
| Apache Airflow | Orchestration pipeline |
| Dash + Plotly | Dashboard temps réel |
| FastAPI | API REST |
| Scikit-learn | Modèle prédiction churn |

## Fonctionnalités
- Pipeline automatique d'insertion de commandes toutes les minutes
- Dashboard temps réel avec KPIs e-commerce
- API REST avec 5 endpoints documentés
- Modèle ML de prédiction churn client

## Lancer le projet

### Prérequis
- Docker
- Python 3.11+
- uv

### Base de données
```bash
docker run --name postgres-ecom \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin123 \
  -e POSTGRES_DB=ecommerce \
  -p 5432:5432 -d postgres:15
```

### Airflow
```bash
docker run --name airflow \
  -p 8080:8080 \
  --link postgres-ecom:postgres \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
  -d apache/airflow:2.8.0 standalone
```

### Dashboard
```bash
uv run python dashboard/app.py
# http://localhost:8050
```

### API
```bash
uvicorn api.main:app --reload --port 8000
# http://localhost:8000/docs
```

### Modèle churn
```bash
uv run python ml/churn_model.py
```

## Screenshots
![Airflow](screenshots/airflow.png)
![API](screenshots/api.png)
![Dashboard](screenshots/dashbord.png)
![Pg](screenshots/pg.png)