from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.recommendation_service import recommendation_service


client = TestClient(app)


def test_recommendations_normal_healthy_assessment() -> None:
    payload = {
        "assessment_input": {
            "age": 30,
            "systolic_bp": 115,
            "diastolic_bp": 75,
            "glucose": 85,
            "hba1c": 5.2,
            "bmi": 21.5,
            "smoking_status": "no",
            "exercise_frequency": "active",
            "sleep_hours": 8,
            "water_intake_l": 2.5,
        },
        "heart": {"risk_score": 0.10, "prediction": 0, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"risk_score": 0.12, "prediction": 0, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"risk_score": 0.15, "prediction": 0, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"risk_score": 0.18, "prediction": 0, "threshold": 0.50, "model": "LightGBM"},
        "risk_fusion": {"overall_risk_score": 0.1375, "overall_risk_level": "low", "top_priority_display_name": "Obesity"},
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_count"] > 0
    categories = [r["category"] for r in data["recommendations"]]
    assert "blood_pressure" not in categories  # Normal BP
    assert "smoking" not in categories  # Non-smoker
    assert "nutrition" in categories or "hydration" in categories  # Baseline guidance


def test_recommendations_high_bp_and_smoking() -> None:
    payload = {
        "assessment_input": {
            "systolic_bp": 160,
            "diastolic_bp": 98,
            "smoking_status": "smoker",
            "exercise_frequency": "inactive",
            "sleep_hours": 5.5,
        },
        "hypertension": {
            "risk_score": 0.9160,
            "prediction": 1,
            "threshold": 0.60,
            "model": "XGBoost",
            "top_contributors": [{"feature": "systolic_bp_mmHg", "contribution": 2.2488, "direction": "increases_risk", "human_readable": "Systolic BP"}],
        },
        "risk_fusion": {"overall_risk_score": 0.85, "overall_risk_level": "very_high", "top_priority_display_name": "Hypertension", "multiple_high_risk": True},
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    categories = [r["category"] for r in data["recommendations"]]
    assert "blood_pressure" in categories
    assert "smoking" in categories
    assert "sleep" in categories
    assert "physical_activity" in categories

    bp_rec = next(r for r in data["recommendations"] if r["category"] == "blood_pressure")
    assert bp_rec["priority"] == "urgent"
    assert "Systolic" in bp_rec["reason"] or "Hypertension" in bp_rec["reason"]

    # Verify priority sorting (urgent first)
    priorities = [r["priority"] for r in data["recommendations"]]
    assert priorities[0] == "urgent"


def test_recommendation_deduplication_and_shap_reasoning() -> None:
    payload = {
        "assessment_input": {
            "glucose": 180,
            "hba1c": 7.2,
            "exercise_frequency": "inactive",
        },
        "diabetes": {
            "risk_score": 0.9037,
            "prediction": 1,
            "threshold": 0.70,
            "model": "LightGBM",
            "top_contributors": [{"feature": "hba1c_level", "contribution": 6.8569, "direction": "increases_risk", "human_readable": "HbA1c Level"}],
        },
        "heart": {"risk_score": 0.82, "prediction": 1, "threshold": 0.40, "model": "XGBoost"},
        "hypertension": {"risk_score": 0.91, "prediction": 1, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"risk_score": 0.74, "prediction": 1, "threshold": 0.50, "model": "LightGBM"},
        "risk_fusion": {"overall_risk_score": 0.84, "overall_risk_level": "very_high", "top_priority_display_name": "Diabetes", "multiple_high_risk": True},
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    # Deduplication check: physical activity recommendation should appear ONLY ONCE despite multiple disease triggers
    act_recs = [r for r in data["recommendations"] if r["category"] == "physical_activity"]
    assert len(act_recs) == 1
    assert "heart" in act_recs[0]["related_diseases"]
    assert "hypertension" in act_recs[0]["related_diseases"]

    # SHAP reasoning check
    gl_rec = next(r for r in data["recommendations"] if r["category"] == "blood_glucose")
    assert "HbA1c" in gl_rec["reason"]
    assert "+6.8569" in gl_rec["reason"] or "contributor" in gl_rec["reason"]


def test_missing_disease_recommendations() -> None:
    payload = {
        "assessment_input": {"systolic_bp": 145, "diastolic_bp": 92},
        "hypertension": {"risk_score": 0.75, "prediction": 1, "threshold": 0.60, "model": "XGBoost"},
        # heart, diabetes, obesity missing
    }

    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_count"] > 0
    assert data["generated_from"]["hypertension"] is True
    assert data["generated_from"]["diabetes"] is False


def test_no_diagnostic_medical_claims() -> None:
    payload = {
        "assessment_input": {"systolic_bp": 150, "glucose": 160},
        "hypertension": {"risk_score": 0.85, "prediction": 1, "threshold": 0.60, "model": "XGBoost"},
    }
    response = client.post("/api/v1/recommendations", json=payload)
    data = response.json()

    for rec in data["recommendations"]:
        full_text = (rec["title"] + rec["description"] + rec["reason"] + rec["action"]).lower()
        assert "you have heart disease" not in full_text
        assert "you are cured" not in full_text
        assert "official medical prescription" not in full_text
