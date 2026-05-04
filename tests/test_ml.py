from unittest.mock import patch

import pandas as pd
import pytest

from ml.churn_model import entrainer_modele, preparer_features


def _make_df(nb: int = 5) -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": range(nb),
        "nom": [f"Client{i}" for i in range(nb)],
        "nb_commandes": [float(i + 1) for i in range(nb)],
        "total_depense": [float((i + 1) * 100) for i in range(nb)],
        "jours_inactif": [float(i * 15) for i in range(nb)],
    })


def test_preparer_features_colonnes():
    df = _make_df()
    result, features = preparer_features(df)
    assert "churn" in result.columns
    assert set(features) == {"nb_commandes", "total_depense", "jours_inactif"}


def test_preparer_features_nulls():
    df = pd.DataFrame({
        "customer_id": [1],
        "nom": ["A"],
        "nb_commandes": [None],
        "total_depense": [None],
        "jours_inactif": [None],
    })
    result, _ = preparer_features(df)
    assert result["nb_commandes"].iloc[0] == 0.0
    assert result["total_depense"].iloc[0] == 0.0
    assert result["jours_inactif"].iloc[0] == 9999.0
    assert result["churn"].iloc[0] == 1


def test_entrainer_modele_classe_unique(tmp_path, monkeypatch):
    """Tous les clients actifs → arrêt propre sans écriture du pkl."""
    df_actifs = _make_df()
    df_actifs["jours_inactif"] = 1.0

    monkeypatch.setenv("CHURN_JOURS_INACTIF", "30")

    with patch("ml.churn_model.get_data", return_value=df_actifs), \
         patch("ml.churn_model.MODEL_PATH", tmp_path / "churn_model.pkl"):
        entrainer_modele()

    assert not (tmp_path / "churn_model.pkl").exists()


def test_entrainer_modele_vide():
    """DataFrame vide → arrêt propre."""
    df_vide = pd.DataFrame(columns=["customer_id", "nom", "nb_commandes", "total_depense", "jours_inactif"])
    with patch("ml.churn_model.get_data", return_value=df_vide):
        entrainer_modele()
