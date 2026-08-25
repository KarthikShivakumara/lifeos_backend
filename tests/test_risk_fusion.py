from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.risk_fusion_service import risk_fusion_service


client = TestClient(app)


def test_fusion_all_low_risk() -> None:
    payload = {
        "heart": {"disease": "heart", "risk_score": 0.15, "prediction": 0, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.20, "prediction": 0, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"disease": "hypertension", "risk_score": 0.10, "prediction": 0, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"disease": "obesity", "risk_score": 0.25, "prediction": 0, "threshold": 0.50, "model": "LightGBM"},
    }
    response = client.post("/api/v1/risk/fusion", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["overall_risk_level"] == "low"
    assert data["overall_risk_score"] == 0.175
    assert data["overall_health_score"] == 82
    assert len(data["disease_ranking"]) == 4
    assert data["multiple_high_risk"] is False


def test_fusion_all_high_risk() -> None:
    payload = {
        "heart": {"disease": "heart", "risk_score": 0.85, "prediction": 1, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.90, "prediction": 1, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"disease": "hypertension", "risk_score": 0.95, "prediction": 1, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"disease": "obesity", "risk_score": 0.88, "prediction": 1, "threshold": 0.50, "model": "LightGBM"},
    }
    response = client.post("/api/v1/risk/fusion", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["overall_risk_level"] == "very_high"
    assert data["top_priority_disease"] == "hypertension"
    assert data["top_priority_score"] == 0.95
    assert data["multiple_high_risk"] is True
    assert data["multiple_very_high_risk"] is True


def test_fusion_mixed_risk_and_ranking() -> None:
    payload = {
        "heart": {"disease": "heart", "risk_score": 0.8248, "prediction": 1, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.9037, "prediction": 1, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"disease": "hypertension", "risk_score": 0.9160, "prediction": 1, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"disease": "obesity", "risk_score": 0.7448, "prediction": 1, "threshold": 0.50, "model": "LightGBM"},
    }
    response = client.post("/api/v1/risk/fusion", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["top_priority_disease"] == "hypertension"
    assert data["disease_ranking"][0]["disease"] == "hypertension"
    assert data["disease_ranking"][1]["disease"] == "diabetes"
    assert data["disease_ranking"][2]["disease"] == "heart"
    assert data["disease_ranking"][3]["disease"] == "obesity"

    # Weighted Average: (0.8248 + 0.9037 + 0.9160 + 0.7448) / 4 = 0.847325 -> 0.8473
    assert data["overall_risk_score"] == 0.8473
    assert data["overall_risk_percentage"] == 84.73
    assert data["overall_health_score"] == 15
    assert data["overall_risk_level"] == "very_high"


def test_fusion_missing_disease_handling() -> None:
    payload = {
        "heart": {"disease": "heart", "risk_score": 0.82, "prediction": 1, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.90, "prediction": 1, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": None,  # Missing disease
        "obesity": {"disease": "obesity", "risk_score": 0.74, "prediction": 1, "threshold": 0.50, "model": "LightGBM"},
    }
    response = client.post("/api/v1/risk/fusion", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["available_diseases_count"] == 3
    assert "hypertension" in data["missing_diseases"]
    assert len(data["disease_ranking"]) == 3
    # Weighted Average across 3 available models: (0.82 + 0.90 + 0.74) / 3 = 0.82
    assert data["overall_risk_score"] == 0.82


def test_direct_api_risk_fusion() -> None:
    payload = {
        "heart": {"disease": "heart", "risk_score": 0.30, "prediction": 0, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.40, "prediction": 0, "threshold": 0.70, "model": "LightGBM"},
    }
    response = client.post("/api/risk/fusion", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["available_diseases_count"] == 2
    assert data["top_priority_disease"] == "diabetes"
