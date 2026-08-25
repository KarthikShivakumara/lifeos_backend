from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.obesity_model_service import obesity_service


client = TestClient(app)


def test_obesity_service_singleton() -> None:
    obesity_service.load_model()
    assert obesity_service.is_loaded is True
    assert obesity_service.model_name == "LightGBM"
    assert obesity_service.threshold == 0.50


def test_valid_obesity_prediction() -> None:
    payload = {
        "age_years": 24.0,
        "sex": 1.0,
        "family_history_obesity": 1.0,
        "frequent_high_calorie_food": 1.0,
        "vegetable_consumption": 2.0,
        "meals_per_day": 3.0,
        "between_meal_eating": 1.0,
        "smoking_status": 0.0,
        "water_intake_l": 2.0,
        "calorie_monitoring": 0.0,
        "physical_activity_frequency": 0.0,
        "technology_usage_hours": 1.0,
        "alcohol_use": 1.0,
        "transportation_mode": 1.0,
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "obesity"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["threshold"] == 0.50
    assert data["prediction"] in [0, 1]
    assert data["model"] == "LightGBM"
    assert data["model_version"] == "1.0.0"


def test_invalid_age() -> None:
    payload = {
        "age_years": 5.0,  # Min 14.0
        "sex": 1.0,
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 422


def test_invalid_sex() -> None:
    payload = {
        "age_years": 25.0,
        "sex": 3.0,  # Max 1.0
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 422


def test_invalid_ranges() -> None:
    payload = {
        "age_years": 25.0,
        "sex": 1.0,
        "vegetable_consumption": 5.0,  # Max 3.0
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 422


def test_missing_required_features() -> None:
    payload = {
        "family_history_obesity": 1.0,
        # missing age_years and sex
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 422


def test_obesity_explanation() -> None:
    payload = {
        "age_years": 24.0,
        "sex": 1.0,
        "family_history_obesity": 1.0,
        "frequent_high_calorie_food": 1.0,
        "vegetable_consumption": 2.0,
        "meals_per_day": 3.0,
        "between_meal_eating": 1.0,
        "smoking_status": 0.0,
        "water_intake_l": 2.0,
        "calorie_monitoring": 0.0,
        "physical_activity_frequency": 0.0,
        "technology_usage_hours": 1.0,
        "alcohol_use": 1.0,
        "transportation_mode": 1.0,
    }
    response = client.post("/api/v1/explain/obesity", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "obesity"
    assert "top_contributors" in data
    assert len(data["top_contributors"]) > 0

    for contrib in data["top_contributors"]:
        assert "feature" in contrib
        assert "contribution" in contrib
        assert contrib["direction"] in ["increases_risk", "decreases_risk"]
        assert "human_readable" in contrib
        # Ensure leakage terms are absent
        assert contrib["feature"] not in ["height", "weight", "bmi", "nobeyesdad"]


def test_obesity_health_endpoint() -> None:
    response = client.get("/api/v1/health/obesity")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["obesity_model"] == "loaded"


def test_direct_api_predict_and_explain() -> None:
    payload = {
        "age_years": 30.0,
        "sex": 0.0,
        "family_history_obesity": 0.0,
        "frequent_high_calorie_food": 0.0,
        "physical_activity_frequency": 2.0,
    }
    resp1 = client.post("/api/predict/obesity", json=payload)
    assert resp1.status_code == 200

    resp2 = client.post("/api/explain/obesity", json=payload)
    assert resp2.status_code == 200
