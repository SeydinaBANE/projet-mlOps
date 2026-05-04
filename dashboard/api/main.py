import logging
import os
import pickle
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="E-commerce API")

_churn_model = None
_MODEL_PATH = Path("ml/churn_model.pkl")


def _load_churn_model():
    global _churn_model
    if _churn_model is None and _MODEL_PATH.exists():
        with open(_MODEL_PATH, "rb") as f:
            _churn_model = pickle.load(f)
    return _churn_model


def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


@app.get("/")
def home():
    return {"message": "API E-commerce opérationnelle"}


@app.get("/ventes")
def ventes():
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT DATE(created_at) AS date,
                   COUNT(*) AS nb_commandes,
                   SUM(montant_total) AS ca
            FROM orders
            WHERE statut = 'completed'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error("Erreur /ventes : %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/clients")
def clients():
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT c.nom, c.pays,
                   COUNT(o.id) AS nb_commandes,
                   SUM(o.montant_total) AS total_depense
            FROM customers c
            JOIN orders o ON o.customer_id = c.id
            WHERE o.statut = 'completed'
            GROUP BY c.nom, c.pays
            ORDER BY total_depense DESC
        """, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error("Erreur /clients : %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/produits")
def produits():
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT p.nom,
                   SUM(oi.quantite) AS qte_vendue,
                   SUM(oi.quantite * oi.prix_unitaire) AS revenu
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            GROUP BY p.nom
            ORDER BY revenu DESC
        """, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error("Erreur /produits : %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/kpis")
def kpis():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders")
        nb_commandes = cur.fetchone()[0]
        cur.execute("SELECT SUM(montant_total) FROM orders WHERE statut='completed'")
        ca_total = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(DISTINCT customer_id) FROM orders")
        nb_clients = cur.fetchone()[0]
        cur.close()
        return {
            "nb_commandes": nb_commandes,
            "ca_total_fcfa": ca_total,
            "nb_clients_actifs": nb_clients,
        }
    except Exception as e:
        logger.error("Erreur /kpis : %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/churn")
def churn():
    model = _load_churn_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non disponible. Lancez d'abord : uv run python ml/churn_model.py",
        )
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT
                c.id AS customer_id,
                c.nom,
                COUNT(o.id) AS nb_commandes,
                COALESCE(SUM(o.montant_total), 0) AS total_depense,
                COALESCE(EXTRACT(EPOCH FROM (NOW() - MAX(o.created_at)))/86400, 9999) AS jours_inactif
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id
            GROUP BY c.id, c.nom
        """, conn)
    except Exception as e:
        logger.error("Erreur /churn : %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    features = ["nb_commandes", "total_depense", "jours_inactif"]
    X = df[features]
    df["risque_churn"] = model.predict(X).tolist()
    proba = model.predict_proba(X)
    df["probabilite_churn"] = proba[:, 1].round(2).tolist() if proba.shape[1] > 1 else [0.0] * len(df)
    return df[["customer_id", "nom", "nb_commandes", "jours_inactif", "risque_churn", "probabilite_churn"]].to_dict(orient="records")
