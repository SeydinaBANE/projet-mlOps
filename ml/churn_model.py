import logging
import os
import pickle
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

CHURN_JOURS_INACTIF = int(os.getenv("CHURN_JOURS_INACTIF", "30"))
MODEL_PATH = Path("ml/churn_model.pkl")


def _db_url() -> str:
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB')}"
    )


def get_data() -> pd.DataFrame:
    engine = create_engine(_db_url())
    return pd.read_sql("""
        SELECT
            c.id AS customer_id,
            c.nom,
            COUNT(o.id) AS nb_commandes,
            SUM(o.montant_total) AS total_depense,
            EXTRACT(EPOCH FROM (NOW() - MAX(o.created_at)))/86400 AS jours_inactif
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, c.nom
    """, engine)


def preparer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    df["nb_commandes"] = df["nb_commandes"].fillna(0)
    df["total_depense"] = df["total_depense"].fillna(0)
    df["jours_inactif"] = df["jours_inactif"].fillna(9999)
    df["churn"] = (df["jours_inactif"] > CHURN_JOURS_INACTIF).astype(int)
    return df, ["nb_commandes", "total_depense", "jours_inactif"]


def entrainer_modele() -> None:
    logger.info("Chargement des données...")
    df = get_data()

    if df.empty:
        logger.error("Aucune donnée trouvée. Vérifiez les tables customers/orders.")
        return

    df, features = preparer_features(df)
    logger.info("\n%s", df[["nom", "nb_commandes", "total_depense", "jours_inactif", "churn"]].to_string())

    X = df[features]
    y = df["churn"]

    if y.nunique() < 2:
        logger.warning(
            "Données insuffisantes : une seule classe présente. "
            "Ajoutez des clients inactifs depuis plus de %d jours.",
            CHURN_JOURS_INACTIF,
        )
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    logger.info("\nRésultats :\n%s", classification_report(y_test, y_pred, zero_division=0))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info("Modèle sauvegardé : %s", MODEL_PATH)

    df["risque_churn"] = model.predict(X)
    proba = model.predict_proba(X)
    df["probabilite_churn"] = proba[:, 1].round(2) if proba.shape[1] > 1 else 0.0
    logger.info("\nPrédictions :\n%s",
        df[["nom", "nb_commandes", "jours_inactif", "risque_churn", "probabilite_churn"]].to_string())


if __name__ == "__main__":
    entrainer_modele()
