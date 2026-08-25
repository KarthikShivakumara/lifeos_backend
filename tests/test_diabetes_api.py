from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.diabetes_model_service import diabetes_service


client = TestClient(app)


def test_diabetes_service_singleton() -> None:
    diabetes_service.load_model()
    assert diabetes_service.is_loaded is True
    assert diabetes_service.model_name == "LightGBM"
    assert diabetes_service.threshold == 0.70


def test_valid_diabetes_prediction() -> None:
    payload = {
        "age_years": 62.0,
        "sex": 1.0,
        "bmi": 30.04,
        "blood_glucose_level": 180.0,
        "hba1c_level": 7.2,
        "hypertension": 1.0,
        "heart_disease": 0.0,
        "smoking_status": 1.0,
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "diabetes"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["threshold"] == 0.70
    assert data["prediction"] in [0, 1]
    assert data["model"] == "LightGBM"
    assert data["model_version"] == "1.0.0"


def test_invalid_age() -> None:
    payload = {
        "age_years": 10.0,  # Min is 18.0
        "sex": 1.0,
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_invalid_bmi() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        "bmi": 120.0,  # Max is 80.0
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_invalid_glucose() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        "blood_glucose_level": 500.0,  # Max is 350.0
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_invalid_hba1c() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        "hba1c_level": 20.0,  # Max is 15.0
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_invalid_binary_field() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 5.0,  # Max is 1.0
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_missing_allowed_features() -> None:
    payload = {
        "age_years": 45.0,
        "sex": 0.0,
        "bmi": 24.5,
        "blood_glucose_level": 95.0,
        # hba1c_level, hypertension, heart_disease, smoking_status omitted
    }
    response = client.post("/api/v1/predict/diabetes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["risk_score"] <= 1.0


def test_diabetes_explanation() -> None:
    payload = {
        "age_years": 62.0,
        "sex": 1.0,
        "bmi": 30.04,
        "blood_glucose_level": 180.0,
        "hba1c_level": 7.2,
        "hypertension": 1.0,
        "heart_disease": 0.0,
        "smoking_status": 1.0,
    }
    response = client.post("/api/v1/explain/diabetes", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "diabetes"
    assert "top_contributors" in data
    assert len(data["top_contributors"]) > 0

    for contrib in data["top_contributors"]:
        assert "feature" in contrib
        assert "contribution" in contrib
        assert contrib["direction"] in ["increases_risk", "decreases_risk"]
        assert "human_readable" in contrib


def test_direct_api_predict_and_explain() -> None:
    payload = {
        "age_years": 55.0,
        "sex": 0.0,
        "bmi": 28.0,
        "blood_glucose_level": 140.0,
        "hba1c_level": 6.5,
    }
    resp1 = client.post("/api/predict/diabetes", json=payload)
    assert resp1.status_code == 200

    resp2 = client.post("/api/explain/diabetes", json=payload)
    assert resp2.status_code == 200
