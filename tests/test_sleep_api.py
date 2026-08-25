from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.sleep_model_service import SleepModelService

client = TestClient(app)
sleep_service = SleepModelService.get_instance()


def test_01_sleep_health_endpoint() -> None:
    response = client.get("/api/v1/health/sleep")
    assert response.status_code == 200
    data = response.json()
    assert data["subsystem"] == "sleep_wellness"
    assert data["model_loaded"] is True
    assert data["status"] == "healthy"
    assert "operating_threshold" in data


def test_02_valid_sleep_prediction() -> None:
    payload = {
        "gender": "Male",
        "age": 30.0,
        "occupation": "Doctor",
        "sleep_duration": 7.8,
        "quality_of_sleep": 7.0,
        "physical_activity_level": 75.0,
        "stress_level": 6.0,
        "bmi_category": "Normal",
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "heart_rate": 70.0,
        "daily_steps": 8000.0,
    }
    response = client.post("/api/v1/predict/sleep", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["subsystem"] == "sleep_wellness"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("low", "moderate", "elevated")
    assert data["threshold"] == sleep_service.operating_threshold
    assert data["prediction"] in (0, 1)
    assert data["model"] == "Logistic Regression"


def test_03_sleep_explanation() -> None:
    payload = {
        "gender": "Female",
        "age": 29.0,
        "occupation": "Nurse",
        "sleep_duration": 6.5,
        "quality_of_sleep": 5.0,
        "physical_activity_level": 40.0,
        "stress_level": 7.0,
        "bmi_category": "Normal Weight",
        "systolic_bp": 132.0,
        "diastolic_bp": 87.0,
        "heart_rate": 80.0,
        "daily_steps": 4000.0,
    }
    response = client.post("/api/v1/explain/sleep", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["subsystem"] == "sleep_wellness"
    assert "base_value" in data
    assert "top_contributions" in data
    assert len(data["top_contributions"]) > 0
    assert "explanation_summary" in data


def test_04_invalid_sleep_payload() -> None:
    payload = {
        "gender": "InvalidGender",
        "age": -10.0,
        "occupation": "Doctor",
        "sleep_duration": 20.0,
        "quality_of_sleep": 15.0,
        "physical_activity_level": 500.0,
        "stress_level": 20.0,
        "bmi_category": "InvalidBMI",
        "systolic_bp": 300.0,
        "diastolic_bp": 200.0,
        "heart_rate": 300.0,
        "daily_steps": 100000.0,
    }
    response = client.post("/api/v1/predict/sleep", json=payload)
    assert response.status_code == 422
