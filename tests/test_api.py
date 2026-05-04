from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    with patch("dashboard.api.main.get_conn"):
        from dashboard.api.main import app
        yield TestClient(app)


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API E-commerce opérationnelle"}


def test_kpis_schema(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [(42,), (10000.0,), (5,)]
    mock_conn.cursor.return_value = mock_cur

    with patch("dashboard.api.main.get_conn", return_value=mock_conn):
        response = client.get("/kpis")

    assert response.status_code == 200
    data = response.json()
    assert data["nb_commandes"] == 42
    assert data["ca_total_fcfa"] == 10000.0
    assert "nb_clients_actifs" in data


def test_kpis_ca_null(client):
    """float(None) ne doit pas planter quand aucune commande completed."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [(0,), (None,), (0,)]
    mock_conn.cursor.return_value = mock_cur

    with patch("dashboard.api.main.get_conn", return_value=mock_conn):
        response = client.get("/kpis")

    assert response.status_code == 200
    assert response.json()["ca_total_fcfa"] == 0.0


def test_churn_model_absent(client):
    """Retourne 503 si le modèle pkl n'existe pas encore."""
    with patch("dashboard.api.main._load_churn_model", return_value=None):
        response = client.get("/churn")
    assert response.status_code == 503
