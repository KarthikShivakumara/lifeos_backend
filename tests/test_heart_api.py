from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest


# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.heart_model_service import heart_service


client = TestClient(app)


def test_01_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["heart_model"] == "loaded"
    assert data["model"] == "XGBoost"
    assert data["version"] == "1.0.0"


def test_02_valid_heart_prediction() -> None:
    payload = {
        "age_years": 54.0,
        "sex": 1.0,
        "height_cm": 168.0,
        "weight_kg": 76.0,
        "bmi": 26.9,
        "systolic_bp_mmHg": 138,
        "diastolic_bp_mmHg": 88.0,
        "smoking_status": 0.0,
        "alcohol_status": 0.0,
        "physical_activity": 1.0,
        "cholesterol_ordinal": 2.0,
        "glucose_ordinal": 1.0,
    }
    response = client.post("/api/predict/heart", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "heart_disease"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("low", "moderate", "high")
    assert data["threshold"] == 0.40
    assert data["prediction"] in (0, 1)
    assert data["model"] == "XGBoost"
    assert data["model_version"] == "1.0.0"


def test_03_invalid_age() -> None:
    payload = {
        "age_years": 10.0,  # Below ge=18.0
        "sex": 1.0,
        "systolic_bp_mmHg": 120,
    }
    response = client.post("/api/predict/heart", json=payload)
    assert response.status_code == 422


def test_04_missing_optional_feature_autoderives_bmi() -> None:
    payload = {
        "age_years": 45.0,
        "sex": 0.0,
        "height_cm": 170.0,
        "weight_kg": 70.0,  # BMI should autoderive to ~24.22
        "systolic_bp_mmHg": 125,
    }
    response = client.post("/api/predict/heart", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data


def test_05_invalid_sex() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 3.0,  # Invalid sex
        "systolic_bp_mmHg": 120,
    }
    response = client.post("/api/predict/heart", json=payload)
    assert response.status_code == 422


def test_06_invalid_blood_pressure() -> None:
    payload = {
        "age_years": 50.0,
        "sex": 1.0,
        "systolic_bp_mmHg": 300,  # Exceeds max=250
    }
    response = client.post("/api/predict/heart", json=payload)
    assert response.status_code == 422


def test_07_model_loading_singleton() -> None:
    s1 = heart_service
    s2 = heart_service
    assert s1 is s2
    assert s1.is_loaded is True


def test_08_shap_explanation_endpoint() -> None:
    payload = {
        "age_years": 62.0,
        "sex": 1.0,
        "height_cm": 175.0,
        "weight_kg": 92.0,
        "bmi": 30.0,
        "systolic_bp_mmHg": 160,
        "diastolic_bp_mmHg": 95.0,
        "smoking_status": 1.0,
        "alcohol_status": 0.0,
        "physical_activity": 0.0,
        "cholesterol_ordinal": 3.0,
        "glucose_ordinal": 2.0,
    }
    response = client.post("/api/explain/heart", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "heart_disease"
    assert "top_contributors" in data
    assert len(data["top_contributors"]) <= 5

    for item in data["top_contributors"]:
        assert "feature" in item
        assert "contribution" in item
        assert item["direction"] in ("increases_risk", "decreases_risk")
        assert "human_readable" in item
