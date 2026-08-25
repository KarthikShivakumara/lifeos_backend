from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.stroke_model_service import StrokeModelService

client = TestClient(app)
stroke_service = StrokeModelService.get_instance()


def test_01_stroke_health_endpoint() -> None:
    response = client.get("/api/v1/health/stroke")
    assert response.status_code == 200
    data = response.json()
    assert data["disease"] == "stroke"
    assert data["model_loaded"] is True
    assert data["status"] == "healthy"
    assert "operating_threshold" in data


def test_02_valid_stroke_prediction() -> None:
    payload = {
        "gender": "Male",
        "age": 67.0,
        "hypertension": 0,
        "heart_disease": 1,
        "ever_married": "Yes",
        "work_type": "Private",
        "Residence_type": "Urban",
        "avg_glucose_level": 228.69,
        "bmi": 36.6,
        "smoking_status": "formerly smoked",
    }
    response = client.post("/api/v1/predict/stroke", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "stroke"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("low", "moderate", "high", "very_high")
    assert data["threshold"] == stroke_service.operating_threshold
    assert data["prediction"] in (0, 1)
    assert data["model"] == "LightGBM"


def test_03_stroke_explanation() -> None:
    payload = {
        "gender": "Female",
        "age": 61.0,
        "hypertension": 0,
        "heart_disease": 0,
        "ever_married": "Yes",
        "work_type": "Self-employed",
        "Residence_type": "Rural",
        "avg_glucose_level": 202.21,
        "bmi": 32.0,
        "smoking_status": "never smoked",
    }
    response = client.post("/api/v1/explain/stroke", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "stroke"
    assert "base_value" in data
    assert "top_contributions" in data
    assert len(data["top_contributions"]) > 0
    assert "explanation_summary" in data


def test_04_invalid_stroke_payload() -> None:
    payload = {
        "gender": "InvalidGender",
        "age": -10.0,
        "hypertension": 5,
        "heart_disease": 0,
        "ever_married": "Maybe",
        "work_type": "Freelance",
        "Residence_type": "Suburbs",
        "avg_glucose_level": 500.0,
        "bmi": 120.0,
        "smoking_status": "Unknown",
    }
    response = client.post("/api/v1/predict/stroke", json=payload)
    assert response.status_code == 422
