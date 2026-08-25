from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.hypertension_model_service import hypertension_service


client = TestClient(app)


def test_hypertension_service_singleton() -> None:
    hypertension_service.load_model()
    assert hypertension_service.is_loaded is True
    assert hypertension_service.model_name == "XGBoost"
    assert hypertension_service.threshold == 0.60


def test_valid_hypertension_prediction() -> None:
    payload = {
        "age_years": 62.0,
        "sex": 1.0,
        "bmi": 30.04,
        "systolic_bp_mmHg": 160.0,
        "diastolic_bp_mmHg": 95.0,
        "heart_rate": 84.0,
        "cholesterol": 250.0,
        "glucose": 180.0,
        "smoking_status": 1.0,
    }
    response = client.post("/api/v1/predict/hypertension", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "hypertension"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["threshold"] == 0.60
    assert data["prediction"] in [0, 1]
    assert data["model"] == "XGBoost"
    assert data["model_version"] == "1.0.0"


def test_invalid_age() -> None:
    payload = {
        "age_years": 10.0,  # Min 18.0
        "sex": 1.0,
        "systolic_bp_mmHg": 130.0,
        "diastolic_bp_mmHg": 85.0,
    }
    response = client.post("/api/v1/predict/hypertension", json=payload)
    assert response.status_code == 422


def test_invalid_sex() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 5.0,  # Max 1.0
        "systolic_bp_mmHg": 130.0,
        "diastolic_bp_mmHg": 85.0,
    }
    response = client.post("/api/v1/predict/hypertension", json=payload)
    assert response.status_code == 422


def test_invalid_bp() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        "systolic_bp_mmHg": 350.0,  # Max 250.0
        "diastolic_bp_mmHg": 85.0,
    }
    response = client.post("/api/v1/predict/hypertension", json=payload)
    assert response.status_code == 422


def test_missing_required_field() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        # missing systolic_bp_mmHg and diastolic_bp_mmHg
    }
    response = client.post("/api/v1/predict/hypertension", json=payload)
    assert response.status_code == 422


def test_hypertension_explanation() -> None:
    payload = {
        "age_years": 62.0,
        "sex": 1.0,
        "bmi": 30.04,
        "systolic_bp_mmHg": 160.0,
        "diastolic_bp_mmHg": 95.0,
        "heart_rate": 84.0,
        "cholesterol": 250.0,
        "glucose": 180.0,
        "smoking_status": 1.0,
    }
    response = client.post("/api/v1/explain/hypertension", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "hypertension"
    assert "top_contributors" in data
    assert len(data["top_contributors"]) > 0

    for contrib in data["top_contributors"]:
        assert "feature" in contrib
        assert "contribution" in contrib
        assert contrib["direction"] in ["increases_risk", "decreases_risk"]
        assert "human_readable" in contrib


def test_hypertension_health_endpoint() -> None:
    response = client.get("/api/v1/health/hypertension")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["hypertension_model"] == "loaded"


def test_direct_api_predict_and_explain() -> None:
    payload = {
        "age_years": 55.0,
        "sex": 0.0,
        "systolic_bp_mmHg": 145.0,
        "diastolic_bp_mmHg": 92.0,
        "bmi": 28.5,
    }
    resp1 = client.post("/api/predict/hypertension", json=payload)
    assert resp1.status_code == 200

    resp2 = client.post("/api/explain/hypertension", json=payload)
    assert resp2.status_code == 200
