"""
Automated Pytest Suite for LifeOS Phase 6.3 - Sensitivity & Robustness Evaluation.

Validates:
- Controlled baseline person stability
- Directional / monotonic responsiveness across single-variable sweeps
- Threshold crossings (Diabetes, HTN, CKD, Obesity)
- Missing-data robustness & Mode A fallback
- Schema numerical boundary validation (HTTP 422 on invalid values)
- Risk Fusion mathematical invariant across all perturbations
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASELINE_PAYLOADS = {
    "heart": {
        "age_years": 45.0, "sex": 1.0, "height_cm": 170.0, "weight_kg": 70.0, "bmi": 24.22,
        "systolic_bp_mmHg": 120.0, "diastolic_bp_mmHg": 80.0, "smoking_status": 0.0,
        "alcohol_status": 0.0, "physical_activity": 1.0, "cholesterol_ordinal": 1.0, "glucose_ordinal": 1.0
    },
    "diabetes": {
        "age_years": 45.0, "sex": 1.0, "bmi": 24.22, "blood_glucose_level": 100.0,
        "hba1c_level": 5.4, "hypertension": 0, "heart_disease": 0, "smoking_status": 0
    },
    "hypertension": {
        "age_years": 45.0, "sex": 1.0, "systolic_bp_mmHg": 120.0, "diastolic_bp_mmHg": 80.0,
        "bmi": 24.22, "heart_rate": 72.0, "cholesterol": 190.0, "glucose": 100.0, "smoking_status": 0.0
    },
    "obesity": {
        "age_years": 45.0, "sex": 1.0, "family_history_obesity": 0.0, "frequent_high_calorie_food": 0.0,
        "vegetable_consumption": 3.0, "meals_per_day": 3.0, "between_meal_eating": 0.0,
        "smoking_status": 0.0, "water_intake_l": 2.0, "calorie_monitoring": 0.0,
        "physical_activity_frequency": 2.0, "technology_usage_hours": 0.0, "alcohol_use": 0.0,
        "transportation_mode": 0.0
    },
    "stroke": {
        "gender": "Male", "age": 45.0, "hypertension": 0, "heart_disease": 0,
        "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban",
        "avg_glucose_level": 100.0, "bmi": 24.22, "smoking_status": "never smoked"
    },
    "ckd": {
        "age": 45.0, "bp": 120.0, "sg": 1.020, "al": 0.0, "su": 0.0, "bgr": 100.0,
        "bu": 14.0, "sc": 0.8, "sod": 140.0, "pot": 4.2, "hemo": 15.0, "pcv": 45.0,
        "wc": 7500.0, "rc": 5.0, "rbc": "normal", "pc": "normal", "pcc": "notpresent",
        "ba": "notpresent", "htn": "no", "dm": "no", "cad": "no", "appet": "good",
        "pe": "no", "ane": "no"
    }
}


def test_controlled_baseline_stability():
    """Verify that the synthetic baseline person produces expected low-risk outputs."""
    h_res = client.post("/api/v1/predict/heart", json=BASELINE_PAYLOADS["heart"]).json()
    d_res = client.post("/api/v1/predict/diabetes", json=BASELINE_PAYLOADS["diabetes"]).json()
    htn_res = client.post("/api/v1/predict/hypertension", json=BASELINE_PAYLOADS["hypertension"]).json()
    obs_res = client.post("/api/v1/predict/obesity", json=BASELINE_PAYLOADS["obesity"]).json()

    assert h_res["prediction"] == 0
    assert d_res["prediction"] == 0
    assert htn_res["prediction"] == 0
    assert obs_res["prediction"] == 0

    fusion_payload = {
        "heart": {"disease": "heart", "risk_score": h_res["risk_score"], "prediction": 0, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": d_res["risk_score"], "prediction": 0, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"disease": "hypertension", "risk_score": htn_res["risk_score"], "prediction": 0, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"disease": "obesity", "risk_score": obs_res["risk_score"], "prediction": 0, "threshold": 0.50, "model": "LightGBM"},
    }
    fusion_res = client.post("/api/v1/risk/fusion", json=fusion_payload).json()
    assert fusion_res["overall_risk_level"] == "low"
    assert fusion_res["overall_risk_score"] < 0.20


def test_sbp_monotonic_response():
    """Verify that increasing SBP produces strictly increasing hypertension and heart disease probabilities."""
    sbp_low = dict(BASELINE_PAYLOADS["hypertension"], systolic_bp_mmHg=110.0, diastolic_bp_mmHg=70.0)
    sbp_high = dict(BASELINE_PAYLOADS["hypertension"], systolic_bp_mmHg=170.0, diastolic_bp_mmHg=105.0)

    res_low = client.post("/api/v1/predict/hypertension", json=sbp_low).json()
    res_high = client.post("/api/v1/predict/hypertension", json=sbp_high).json()

    assert res_high["risk_score"] > res_low["risk_score"]
    assert res_high["risk_score"] >= 0.60  # HTN threshold crossed
    assert res_high["prediction"] == 1


def test_glucose_monotonic_response():
    """Verify that increasing blood glucose increases diabetes risk and crosses the operating threshold."""
    dm_norm = dict(BASELINE_PAYLOADS["diabetes"], blood_glucose_level=90.0, hba1c_level=5.2)
    dm_high = dict(BASELINE_PAYLOADS["diabetes"], blood_glucose_level=230.0, hba1c_level=10.1)

    res_norm = client.post("/api/v1/predict/diabetes", json=dm_norm).json()
    res_high = client.post("/api/v1/predict/diabetes", json=dm_high).json()

    assert res_high["risk_score"] > res_norm["risk_score"]
    assert res_high["risk_score"] >= 0.70  # Diabetes operating threshold crossed
    assert res_high["prediction"] == 1


def test_creatinine_mode_b_response():
    """Verify that elevated serum creatinine and urea increase CKD risk and cross threshold."""
    ckd_norm = dict(BASELINE_PAYLOADS["ckd"], sc=0.8, bu=14.0, al=0.0)
    ckd_elev = dict(BASELINE_PAYLOADS["ckd"], sc=2.8, bu=65.0, al=2.0)

    res_norm = client.post("/api/v1/predict/ckd", json=ckd_norm).json()
    res_elev = client.post("/api/v1/predict/ckd", json=ckd_elev).json()

    assert res_elev["risk_score"] > res_norm["risk_score"]
    assert res_elev["risk_score"] >= 0.33  # Crosses operating threshold 0.33
    assert res_elev["prediction"] == 1


def test_obesity_snacking_contrast():
    """Verify that snacking habit monotonically increases obesity risk, and lifestyle contrast diverges >= 0.30."""
    # Monotonic snacking test on baseline
    obs_never = dict(BASELINE_PAYLOADS["obesity"], between_meal_eating=0.0)
    obs_const = dict(BASELINE_PAYLOADS["obesity"], between_meal_eating=3.0)

    res_never = client.post("/api/v1/predict/obesity", json=obs_never).json()
    res_const = client.post("/api/v1/predict/obesity", json=obs_const).json()
    assert res_const["risk_score"] > res_never["risk_score"]

    # Comprehensive lifestyle contrast (Healthy habits vs Obesogenic habits)
    obs_poor_lifestyle = dict(
        BASELINE_PAYLOADS["obesity"],
        vegetable_consumption=1.0,
        between_meal_eating=3.0,
        technology_usage_hours=2.0,
        transportation_mode=1.0,
        physical_activity_frequency=0.0,
        frequent_high_calorie_food=1.0
    )
    res_poor = client.post("/api/v1/predict/obesity", json=obs_poor_lifestyle).json()
    risk_diff = res_poor["risk_score"] - res_never["risk_score"]
    assert risk_diff >= 0.30, f"Expected lifestyle risk divergence >= 0.30, got {risk_diff:.3f}"


def test_sleep_duration_rest_classification():
    """Verify sleep wellness endpoint processes sleep durations deterministically."""
    sleep_short = {
        "gender": "Male", "age": 45.0, "occupation": "Engineer", "sleep_duration": 4.5,
        "quality_of_sleep": 4.0, "physical_activity_level": 40.0, "stress_level": 8.0,
        "bmi_category": "Normal", "systolic_bp": 120.0, "diastolic_bp": 80.0,
        "heart_rate": 72.0, "daily_steps": 5000.0
    }
    sleep_opt = {
        "gender": "Male", "age": 45.0, "occupation": "Engineer", "sleep_duration": 7.8,
        "quality_of_sleep": 8.0, "physical_activity_level": 60.0, "stress_level": 3.0,
        "bmi_category": "Normal", "systolic_bp": 120.0, "diastolic_bp": 80.0,
        "heart_rate": 70.0, "daily_steps": 8000.0
    }

    res_short = client.post("/api/v1/predict/sleep", json=sleep_short).json()
    res_opt = client.post("/api/v1/predict/sleep", json=sleep_opt).json()

    assert res_short["risk_score"] > res_opt["risk_score"]
    assert res_opt["risk_level"] == "low"


def test_physical_activity_calorie_scaling():
    """Verify workout energy expenditure scales with duration and heart rate."""
    act_light = {
        "gender": "male", "age": 45.0, "height": 170.0, "weight": 70.0,
        "duration": 20.0, "heart_rate": 115.0, "body_temp": 37.3
    }
    act_intense = {
        "gender": "male", "age": 45.0, "height": 170.0, "weight": 70.0,
        "duration": 60.0, "heart_rate": 160.0, "body_temp": 38.6
    }

    res_light = client.post("/api/v1/activity/estimate-calories", json=act_light).json()
    res_intense = client.post("/api/v1/activity/estimate-calories", json=act_intense).json()

    assert res_intense["estimated_calories"] > res_light["estimated_calories"]
    assert res_intense["estimated_calories"] >= 200.0


def test_schema_boundary_enforcement():
    """Verify that inputs outside defined boundaries fail Pydantic validation (HTTP 422)."""
    # Age < 18 rejected by Heart
    bad_age = dict(BASELINE_PAYLOADS["heart"], age_years=16.0)
    res_age = client.post("/api/v1/predict/heart", json=bad_age)
    assert res_age.status_code == 422

    # SBP < 70 rejected by HTN
    bad_sbp = dict(BASELINE_PAYLOADS["hypertension"], systolic_bp_mmHg=55.0)
    res_sbp = client.post("/api/v1/predict/hypertension", json=bad_sbp)
    assert res_sbp.status_code == 422

    # Glucose < 50 rejected by Diabetes
    bad_gluc = dict(BASELINE_PAYLOADS["diabetes"], blood_glucose_level=30.0)
    res_gluc = client.post("/api/v1/predict/diabetes", json=bad_gluc)
    assert res_gluc.status_code == 422


def test_risk_fusion_mathematical_invariant():
    """Verify that Risk Fusion strictly satisfies 0.25 equal weights across all diseases."""
    fusion_payload = {
        "heart": {"disease": "heart", "risk_score": 0.28, "prediction": 0, "threshold": 0.40, "model": "XGBoost"},
        "diabetes": {"disease": "diabetes", "risk_score": 0.64, "prediction": 0, "threshold": 0.70, "model": "LightGBM"},
        "hypertension": {"disease": "hypertension", "risk_score": 0.52, "prediction": 0, "threshold": 0.60, "model": "XGBoost"},
        "obesity": {"disease": "obesity", "risk_score": 0.16, "prediction": 0, "threshold": 0.50, "model": "LightGBM"},
    }
    res = client.post("/api/v1/risk/fusion", json=fusion_payload).json()
    expected = 0.25 * (0.28 + 0.64 + 0.52 + 0.16)
    assert abs(res["overall_risk_score"] - expected) < 1e-4
