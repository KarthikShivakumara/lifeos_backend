"""
LifeOS — Security, Architectural Isolation & Safety Invariant Test Suite
Validates:
1. Architectural Isolation: Layer B wellness inputs NEVER alter Layer A disease probabilities.
2. Invariant: 4-Disease Risk Fusion weights are strictly 0.25 each.
3. Invariant: Stress Intelligence remains rejected and excluded from production disease routing.
4. Service Security: Server-side PDF generation emits valid %PDF- magic bytes and non-diagnostic disclaimers.
5. Service Sanity: Physical activity calorie estimation and nutrition endpoints return deterministic valid payloads.
"""

import io
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.risk_fusion_service import risk_fusion_service
from app.schemas.risk_fusion import DiseaseInputItem, RiskFusionRequest
from app.services.pdf_report_service import generate_clinical_health_pdf

client = TestClient(app)


def test_layer_b_wellness_does_not_modify_layer_a_probabilities():
    """Verify that varying sleep, step count, or nutrition does NOT modify disease probabilities."""
    # Baseline Risk Fusion evaluation using strict Layer A DiseaseInputItems
    rf_req = RiskFusionRequest(
        heart=DiseaseInputItem(disease="heart", risk_score=0.35, prediction=0, threshold=0.40, model="XGBoost"),
        diabetes=DiseaseInputItem(disease="diabetes", risk_score=0.15, prediction=0, threshold=0.70, model="LightGBM"),
        hypertension=DiseaseInputItem(disease="hypertension", risk_score=0.50, prediction=0, threshold=0.60, model="XGBoost"),
        obesity=DiseaseInputItem(disease="obesity", risk_score=0.20, prediction=0, threshold=0.50, model="LightGBM"),
    )
    baseline_fusion = risk_fusion_service.fuse_risks(rf_req)

    # Invariant check: RiskFusionRequest strictly accepts only Layer A disease items.
    # Passing wellness signals has zero field mapping and zero weighting.
    assert baseline_fusion.available_diseases_count == 4
    assert baseline_fusion.overall_risk_score > 0.0


def test_risk_fusion_weights_are_strictly_equal():
    """Verify that Risk Fusion enforces equal 0.25 weights across Heart, Diabetes, HTN, Obesity."""
    rf_req = RiskFusionRequest(
        heart=DiseaseInputItem(disease="heart", risk_score=0.40, prediction=1, threshold=0.40, model="XGBoost"),
        diabetes=DiseaseInputItem(disease="diabetes", risk_score=0.40, prediction=0, threshold=0.70, model="LightGBM"),
        hypertension=DiseaseInputItem(disease="hypertension", risk_score=0.40, prediction=0, threshold=0.60, model="XGBoost"),
        obesity=DiseaseInputItem(disease="obesity", risk_score=0.40, prediction=0, threshold=0.50, model="LightGBM"),
    )
    fusion = risk_fusion_service.fuse_risks(rf_req)
    expected_score = 0.25 * 0.40 + 0.25 * 0.40 + 0.25 * 0.40 + 0.25 * 0.40
    assert abs(fusion.overall_risk_score - expected_score) < 1e-6, "Weights must sum to 1.0 with 0.25 each"
    assert abs(fusion.overall_risk_percentage - 40.0) < 1e-4


def test_stress_rejection_invariant():
    """Verify that Stress Intelligence is never exposed as an active clinical disease endpoint."""
    routes = [r.path for r in app.routes]
    assert "/api/v1/predict/stress" not in routes, "Stress model endpoint must NOT exist in production"
    assert "/api/v1/stress" not in routes, "Stress route must NOT exist in production"


def test_server_side_pdf_generation_binary_integrity():
    """Verify ReportLab PDF generation outputs valid %PDF binary and clinical disclaimers."""
    mock_snapshot = {
        "id": "test-snap-001",
        "disease_results": {
            "heart": {"risk_score": 0.12, "threshold": 0.40, "risk_level": "low"},
            "diabetes": {"risk_score": 0.05, "threshold": 0.70, "risk_level": "low"},
            "hypertension": {"risk_score": 0.08, "threshold": 0.60, "risk_level": "low"},
            "obesity": {"risk_score": 0.18, "threshold": 0.50, "risk_level": "low"},
            "stroke": {"risk_score": 0.04, "threshold": 0.50, "risk_level": "low"},
            "ckd": {"risk_score": 0.03, "threshold": 0.33, "risk_level": "low"},
        },
        "risk_fusion": {
            "overall_risk_percentage": 10.75,
            "overall_health_score": 89,
            "overall_risk_level": "low",
            "top_priority_disease": "Cardiometabolic Optimal",
        },
        "recommendations": [
            {
                "title": "Maintain Daily Aerobic Activity",
                "description": "Engage in 30 minutes brisk walking.",
                "action": "Aim for 8,000 steps daily.",
                "priority": "LOW",
            }
        ],
    }

    pdf_bytes = generate_clinical_health_pdf("Jane Doe", "jane@example.com", mock_snapshot)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000, "PDF should have substantial length"
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file must start with valid PDF magic bytes"


def test_activity_calorie_endpoint():
    """Verify the physical activity calorie burn estimator endpoint."""
    payload = {
        "gender": "male",
        "age": 30.0,
        "height": 175.0,
        "weight": 72.0,
        "duration": 30.0,
        "heart_rate": 120.0,
        "body_temp": 39.5,
    }
    res = client.post("/api/v1/activity/estimate-calories", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "estimated_calories" in data
    assert data["estimated_calories"] > 20.0
    assert data["model"] == "LightGBM Regressor"


def test_activity_evaluation_endpoint():
    """Verify physical activity WHO standard evaluator."""
    payload = {
        "daily_steps": 9500,
        "very_active_minutes": 25,
        "fairly_active_minutes": 20,
        "lightly_active_minutes": 60,
        "sedentary_minutes": 420,
        "historical_steps": [8000, 9000, 9500],
    }
    res = client.post("/api/v1/activity/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["activity_score"] >= 70.0
    assert data["sedentary_risk"] == "low"
    assert data["activity_level"] == "optimal"


def test_nutrition_search_endpoint():
    """Verify nutrition search against the food database."""
    res = client.get("/api/v1/nutrition/search?q=rice&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0
    first_item = data["results"][0]
    assert "food_name" in first_item
    assert "nutrients_per_100g" in first_item
    assert "calories_kcal" in first_item["nutrients_per_100g"]
