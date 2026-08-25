from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.ckd_model_service import CKDModelService

client = TestClient(app)
ckd_service = CKDModelService.get_instance()


def test_01_ckd_health_endpoint() -> None:
    response = client.get("/api/v1/health/ckd")
    assert response.status_code == 200
    data = response.json()
    assert data["disease"] == "ckd"
    assert data["model_loaded"] is True
    assert data["status"] == "healthy"
    assert "operating_threshold" in data


def test_02_valid_ckd_prediction() -> None:
    payload = {
        "age": 48.0,
        "bp": 80.0,
        "sg": 1.020,
        "al": 1.0,
        "su": 0.0,
        "bgr": 121.0,
        "bu": 36.0,
        "sc": 1.2,
        "sod": 135.0,
        "pot": 4.5,
        "hemo": 15.4,
        "pcv": 44.0,
        "wc": 7800.0,
        "rc": 5.2,
        "rbc": "normal",
        "pc": "normal",
        "pcc": "notpresent",
        "ba": "notpresent",
        "htn": "yes",
        "dm": "yes",
        "cad": "no",
        "appet": "good",
        "pe": "no",
        "ane": "no",
    }
    response = client.post("/api/v1/predict/ckd", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "ckd"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("low", "moderate", "high", "very_high")
    assert data["threshold"] == ckd_service.operating_threshold
    assert data["prediction"] in (0, 1)
    assert data["model"] == "XGBoost"


def test_03_ckd_explanation() -> None:
    payload = {
        "age": 62.0,
        "bp": 80.0,
        "sg": 1.010,
        "al": 2.0,
        "su": 3.0,
        "bgr": 423.0,
        "bu": 53.0,
        "sc": 1.8,
        "sod": 130.0,
        "pot": 4.0,
        "hemo": 9.6,
        "pcv": 31.0,
        "wc": 7500.0,
        "rc": 3.9,
        "rbc": "normal",
        "pc": "normal",
        "pcc": "notpresent",
        "ba": "notpresent",
        "htn": "no",
        "dm": "yes",
        "cad": "no",
        "appet": "poor",
        "pe": "no",
        "ane": "yes",
    }
    response = client.post("/api/v1/explain/ckd", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["disease"] == "ckd"
    assert "base_value" in data
    assert "top_contributions" in data
    assert len(data["top_contributions"]) > 0
    assert "explanation_summary" in data


def test_04_invalid_ckd_payload() -> None:
    payload = {
        "age": -5.0,
        "bp": 300.0,
        "sg": 2.0,
        "al": 10.0,
        "su": 10.0,
        "bgr": 1000.0,
        "bu": 500.0,
        "sc": 50.0,
        "sod": 200.0,
        "pot": 20.0,
        "hemo": 30.0,
        "pcv": 100.0,
        "wc": 100000.0,
        "rc": 20.0,
        "rbc": "invalid",
        "pc": "invalid",
        "pcc": "invalid",
        "ba": "invalid",
        "htn": "invalid",
        "dm": "invalid",
        "cad": "invalid",
        "appet": "invalid",
        "pe": "invalid",
        "ane": "invalid",
    }
    response = client.post("/api/v1/predict/ckd", json=payload)
    assert response.status_code == 422
