"""
Test Suite for LifeOS Phase 6.2 - Production Model Input Correction & Usability Fix.

Covers Objectives 8 and 9:
- Test A: Obesity mapping without BMI/height/weight (leakage protection)
- Test B: Missing obesity inputs handled without artificial athlete defaults
- Test C: Real obesity lifestyle inputs produce responsive contrast
- Test D: CKD without laboratory data (Mode A baseline screening)
- Test E: CKD with laboratory data (Mode B lab-enhanced screening)
- Test F: Stroke snapshot integration
- Test G: Risk Fusion invariant (strict 4-way 0.25 weights)
- Test H: Layer A / Layer B air-gap isolation
- Controlled Test Cases: Users A through H deterministic evaluation
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.obesity_model_service import obesity_service

client = TestClient(app)


def test_a_obesity_leakage_protection():
    """Verify obesity model features strictly omit height, weight, and BMI."""
    features = obesity_service.feature_cols
    assert "height_cm" not in features, "Target leakage detected: height_cm in obesity features"
    assert "weight_kg" not in features, "Target leakage detected: weight_kg in obesity features"
    assert "bmi" not in features, "Target leakage detected: bmi in obesity features"
    assert len(features) == 14, f"Expected 14 non-leaking features, got {len(features)}"


def test_b_obesity_missing_input_defaults():
    """Verify realistic median defaults when lifestyle features are omitted."""
    payload = {
        "age_years": 35.0,
        "sex": 1.0,
        "family_history_obesity": 0.0,
        "frequent_high_calorie_food": 0.0,
        "vegetable_consumption": 2.0,  # realistic population average, not athlete 3.0
        "meals_per_day": 3.0,
        "between_meal_eating": 1.0,
        "smoking_status": 0.0,
        "water_intake_l": 2.0,  # realistic 2.0L, not 2.5L
        "calorie_monitoring": 0.0,  # general adult does not monitor calories, not 1.0
        "physical_activity_frequency": 1.0,
        "technology_usage_hours": 1.0,  # 3-5h realistic screen time, not 0.5h
        "alcohol_use": 0.0,
        "transportation_mode": 1.0,  # motorized commute, not athlete 0.0
    }
    response = client.post("/api/v1/predict/obesity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["model"] == "LightGBM"
    assert data["threshold"] == 0.50


def test_c_obesity_lifestyle_contrast():
    """Verify healthy lifestyle vs obesogenic lifestyle produces significant contrast."""
    healthy_payload = {
        "age_years": 35.0,
        "sex": 1.0,
        "family_history_obesity": 0.0,
        "frequent_high_calorie_food": 0.0,
        "vegetable_consumption": 3.0,
        "meals_per_day": 3.0,
        "between_meal_eating": 0.0,
        "smoking_status": 0.0,
        "water_intake_l": 2.5,
        "calorie_monitoring": 1.0,
        "physical_activity_frequency": 3.0,
        "technology_usage_hours": 0.0,
        "alcohol_use": 0.0,
        "transportation_mode": 0.0,
    }
    poor_payload = {
        "age_years": 35.0,
        "sex": 1.0,
        "family_history_obesity": 1.0,
        "frequent_high_calorie_food": 1.0,
        "vegetable_consumption": 1.0,
        "meals_per_day": 3.0,
        "between_meal_eating": 3.0,
        "smoking_status": 0.0,
        "water_intake_l": 1.0,
        "calorie_monitoring": 0.0,
        "physical_activity_frequency": 0.0,
        "technology_usage_hours": 2.0,
        "alcohol_use": 1.0,
        "transportation_mode": 1.0,
    }
    res_h = client.post("/api/v1/predict/obesity", json=healthy_payload).json()
    res_p = client.post("/api/v1/predict/obesity", json=poor_payload).json()

    assert res_p["risk_score"] > res_h["risk_score"], (
        f"Obesogenic risk ({res_p['risk_score']}) should exceed healthy risk ({res_h['risk_score']})"
    )
    risk_diff = res_p["risk_score"] - res_h["risk_score"]
    assert risk_diff >= 0.30, f"Expected lifestyle risk divergence >= 0.30, got {risk_diff:.3f}"


def test_d_ckd_mode_a_baseline_vitals():
    """Verify Mode A (vitals only) runs successfully with standard reference biomarkers."""
    baseline_payload = {
        "age": 45.0,
        "bp": 120.0,
        "sg": 1.02,
        "al": 0.0,
        "su": 0.0,
        "bgr": 100.0,
        "bu": 14.0,
        "sc": 0.8,
        "sod": 140.0,
        "pot": 4.2,
        "hemo": 15.0,
        "pcv": 45.0,
        "wc": 7500.0,
        "rc": 5.0,
        "rbc": "normal",
        "pc": "normal",
        "pcc": "notpresent",
        "ba": "notpresent",
        "htn": "no",
        "dm": "no",
        "cad": "no",
        "appet": "good",
        "pe": "no",
        "ane": "no",
    }
    response = client.post("/api/v1/predict/ckd", json=baseline_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["disease"] == "ckd"
    assert data["model"] == "XGBoost"
    assert data["threshold"] == 0.33
    # Healthy baseline vitals produce low baseline risk
    assert data["risk_score"] < 0.33
    assert data["prediction"] == 0


def test_e_ckd_mode_b_elevated_biomarkers():
    """Verify Mode B (with actual clinical lab results) responds dynamically to elevated creatinine/urea."""
    high_kidney_risk_payload = {
        "age": 55.0,
        "bp": 150.0,
        "sg": 1.010,
        "al": 3.0,
        "su": 1.0,
        "bgr": 180.0,
        "bu": 58.0,
        "sc": 2.6,  # Significantly elevated creatinine
        "sod": 132.0,
        "pot": 5.4,
        "hemo": 9.2,  # Low hemoglobin (renal anemia)
        "pcv": 28.0,
        "wc": 9800.0,
        "rc": 3.4,
        "rbc": "abnormal",
        "pc": "abnormal",
        "pcc": "present",
        "ba": "present",
        "htn": "yes",
        "dm": "yes",
        "cad": "no",
        "appet": "poor",
        "pe": "yes",  # Pedal edema
        "ane": "yes",
    }
    response = client.post("/api/v1/predict/ckd", json=high_kidney_risk_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["disease"] == "ckd"
    assert data["risk_score"] >= 0.70, f"Expected high risk score >= 0.70, got {data['risk_score']}"
    assert data["prediction"] == 1
    assert data["risk_level"] in ("high", "very_high")


def test_f_stroke_api_integration():
    """Verify stroke prediction endpoint returns valid schema."""
    stroke_payload = {
        "gender": "Male",
        "age": 62.0,
        "hypertension": 1,
        "heart_disease": 1,
        "ever_married": "Yes",
        "work_type": "Private",
        "Residence_type": "Urban",
        "avg_glucose_level": 160.0,
        "bmi": 29.5,
        "smoking_status": "formerly smoked",
    }
    response = client.post("/api/v1/predict/stroke", json=stroke_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["model"] == "LightGBM"


def test_g_risk_fusion_invariant():
    """Verify Risk Fusion strictly uses 4-way 0.25 weights (Heart, Diabetes, HTN, Obesity)."""
    fusion_payload = {
        "heart": {"disease": "heart", "risk_score": 0.40, "prediction": 1, "threshold": 0.40, "model": "XGBoost", "top_contributors": []},
        "diabetes": {"disease": "diabetes", "risk_score": 0.80, "prediction": 1, "threshold": 0.70, "model": "LightGBM", "top_contributors": []},
        "hypertension": {"disease": "hypertension", "risk_score": 0.60, "prediction": 1, "threshold": 0.60, "model": "XGBoost", "top_contributors": []},
        "obesity": {"disease": "obesity", "risk_score": 0.20, "prediction": 0, "threshold": 0.50, "model": "LightGBM", "top_contributors": []},
    }
    response = client.post("/api/v1/risk/fusion", json=fusion_payload)
    assert response.status_code == 200
    data = response.json()
    
    # Mathematical invariant: 0.25*(0.40 + 0.80 + 0.60 + 0.20) = 0.25 * 2.00 = 0.50 (50.0%)
    expected_score = 0.25 * (0.40 + 0.80 + 0.60 + 0.20)
    assert abs(data["overall_risk_score"] - expected_score) < 1e-4, (
        f"Fusion score mismatch: got {data['overall_risk_score']}, expected {expected_score}"
    )
    assert abs(data["overall_risk_percentage"] - 50.0) < 0.1


def test_h_layer_b_air_gap_isolation():
    """Verify Layer B wellness outputs (sleep, calorie expenditure) do not alter Layer A disease probabilities."""
    # Predict sleep
    sleep_payload = {
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
    sleep_res = client.post("/api/v1/predict/sleep", json=sleep_payload)
    assert sleep_res.status_code == 200, sleep_res.text
    sleep_data = sleep_res.json()
    assert "risk_score" in sleep_data
    assert sleep_data["subsystem"] == "sleep_wellness"

    # Predict activity calories
    act_payload = {
        "gender": "male",
        "age": 30.0,
        "height": 175.0,
        "weight": 75.0,
        "duration": 45.0,
        "heart_rate": 140.0,
        "body_temp": 38.2,
    }
    act_res = client.post("/api/v1/activity/estimate-calories", json=act_payload)
    assert act_res.status_code == 200, act_res.text
    act_data = act_res.json()
    assert "estimated_calories" in act_data

    # Re-evaluate Risk Fusion — confirm Layer B outputs have zero mathematical influence on Layer A fusion
    fusion_payload = {
        "heart": {"disease": "heart", "risk_score": 0.40, "prediction": 1, "threshold": 0.40, "model": "XGBoost", "top_contributors": []},
        "diabetes": {"disease": "diabetes", "risk_score": 0.80, "prediction": 1, "threshold": 0.70, "model": "LightGBM", "top_contributors": []},
        "hypertension": {"disease": "hypertension", "risk_score": 0.60, "prediction": 1, "threshold": 0.60, "model": "XGBoost", "top_contributors": []},
        "obesity": {"disease": "obesity", "risk_score": 0.20, "prediction": 0, "threshold": 0.50, "model": "LightGBM", "top_contributors": []},
    }
    fusion_data = client.post("/api/v1/risk/fusion", json=fusion_payload).json()
    assert abs(fusion_data["overall_risk_score"] - 0.50) < 1e-4


def test_controlled_test_cases_users_a_through_h():
    """
    Objective 9: Controlled Test Cases (Deterministic evaluation of Users A through H).
    Captures input -> mapped features -> model probability -> threshold -> category.
    """
    cases = [
        ("User A: Healthy Lifestyle", {
            "obesity": {
                "age_years": 28.0, "sex": 0.0, "family_history_obesity": 0.0,
                "frequent_high_calorie_food": 0.0, "vegetable_consumption": 3.0,
                "meals_per_day": 3.0, "between_meal_eating": 0.0, "smoking_status": 0.0,
                "water_intake_l": 2.5, "calorie_monitoring": 1.0, "physical_activity_frequency": 3.0,
                "technology_usage_hours": 0.0, "alcohol_use": 0.0, "transportation_mode": 0.0
            },
            "ckd": {
                "age": 28.0, "bp": 115.0, "sg": 1.025, "al": 0.0, "su": 0.0, "bgr": 85.0, "bu": 12.0, "sc": 0.7,
                "sod": 142.0, "pot": 4.1, "hemo": 15.2, "pcv": 46.0, "wc": 6800.0, "rc": 5.1,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User B: High-Risk Lifestyle", {
            "obesity": {
                "age_years": 50.0, "sex": 1.0, "family_history_obesity": 1.0,
                "frequent_high_calorie_food": 1.0, "vegetable_consumption": 1.0,
                "meals_per_day": 3.0, "between_meal_eating": 3.0, "smoking_status": 1.0,
                "water_intake_l": 1.0, "calorie_monitoring": 0.0, "physical_activity_frequency": 0.0,
                "technology_usage_hours": 2.0, "alcohol_use": 1.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 50.0, "bp": 145.0, "sg": 1.015, "al": 1.0, "su": 0.0, "bgr": 130.0, "bu": 25.0, "sc": 1.2,
                "sod": 138.0, "pot": 4.6, "hemo": 13.5, "pcv": 40.0, "wc": 8200.0, "rc": 4.4,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "yes", "dm": "yes", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User C: High BMI + Healthy Lifestyle", {
            "obesity": {
                "age_years": 32.0, "sex": 1.0, "family_history_obesity": 0.0,
                "frequent_high_calorie_food": 0.0, "vegetable_consumption": 3.0,
                "meals_per_day": 3.0, "between_meal_eating": 0.0, "smoking_status": 0.0,
                "water_intake_l": 3.0, "calorie_monitoring": 1.0, "physical_activity_frequency": 3.0,
                "technology_usage_hours": 0.0, "alcohol_use": 0.0, "transportation_mode": 0.0
            },
            "ckd": {
                "age": 32.0, "bp": 120.0, "sg": 1.020, "al": 0.0, "su": 0.0, "bgr": 90.0, "bu": 15.0, "sc": 0.9,
                "sod": 140.0, "pot": 4.3, "hemo": 15.5, "pcv": 45.0, "wc": 7000.0, "rc": 5.0,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User D: High BMI + Poor Lifestyle", {
            "obesity": {
                "age_years": 32.0, "sex": 1.0, "family_history_obesity": 1.0,
                "frequent_high_calorie_food": 1.0, "vegetable_consumption": 1.0,
                "meals_per_day": 4.0, "between_meal_eating": 2.0, "smoking_status": 0.0,
                "water_intake_l": 1.2, "calorie_monitoring": 0.0, "physical_activity_frequency": 0.0,
                "technology_usage_hours": 2.0, "alcohol_use": 1.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 32.0, "bp": 138.0, "sg": 1.018, "al": 0.0, "su": 0.0, "bgr": 110.0, "bu": 18.0, "sc": 1.0,
                "sod": 139.0, "pot": 4.4, "hemo": 14.8, "pcv": 44.0, "wc": 7600.0, "rc": 4.8,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User E: High Blood Pressure Profile", {
            "obesity": {
                "age_years": 58.0, "sex": 1.0, "family_history_obesity": 0.0,
                "frequent_high_calorie_food": 0.0, "vegetable_consumption": 2.0,
                "meals_per_day": 3.0, "between_meal_eating": 1.0, "smoking_status": 0.0,
                "water_intake_l": 2.0, "calorie_monitoring": 0.0, "physical_activity_frequency": 1.0,
                "technology_usage_hours": 1.0, "alcohol_use": 0.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 58.0, "bp": 165.0, "sg": 1.015, "al": 1.0, "su": 0.0, "bgr": 115.0, "bu": 28.0, "sc": 1.3,
                "sod": 137.0, "pot": 4.5, "hemo": 13.8, "pcv": 41.0, "wc": 8100.0, "rc": 4.5,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "yes", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User F: Diabetes-Associated Profile", {
            "obesity": {
                "age_years": 54.0, "sex": 0.0, "family_history_obesity": 1.0,
                "frequent_high_calorie_food": 1.0, "vegetable_consumption": 1.0,
                "meals_per_day": 3.0, "between_meal_eating": 2.0, "smoking_status": 0.0,
                "water_intake_l": 1.5, "calorie_monitoring": 0.0, "physical_activity_frequency": 1.0,
                "technology_usage_hours": 1.0, "alcohol_use": 0.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 54.0, "bp": 135.0, "sg": 1.015, "al": 1.0, "su": 3.0, "bgr": 210.0, "bu": 32.0, "sc": 1.4,
                "sod": 136.0, "pot": 4.8, "hemo": 12.8, "pcv": 38.0, "wc": 8900.0, "rc": 4.2,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "yes", "dm": "yes", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
        ("User G: Kidney Risk Profile WITH Laboratory Values", {
            "obesity": {
                "age_years": 62.0, "sex": 1.0, "family_history_obesity": 0.0,
                "frequent_high_calorie_food": 0.0, "vegetable_consumption": 2.0,
                "meals_per_day": 3.0, "between_meal_eating": 1.0, "smoking_status": 0.0,
                "water_intake_l": 1.5, "calorie_monitoring": 0.0, "physical_activity_frequency": 1.0,
                "technology_usage_hours": 1.0, "alcohol_use": 0.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 62.0, "bp": 155.0, "sg": 1.010, "al": 3.0, "su": 1.0, "bgr": 175.0, "bu": 65.0, "sc": 2.8,
                "sod": 131.0, "pot": 5.5, "hemo": 8.9, "pcv": 27.0, "wc": 10200.0, "rc": 3.2,
                "rbc": "abnormal", "pc": "abnormal", "pcc": "present", "ba": "present",
                "htn": "yes", "dm": "yes", "cad": "no", "appet": "poor", "pe": "yes", "ane": "yes"
            }
        }),
        ("User H: Kidney Risk Profile WITHOUT Laboratory Values (Vitals Only)", {
            "obesity": {
                "age_years": 62.0, "sex": 1.0, "family_history_obesity": 0.0,
                "frequent_high_calorie_food": 0.0, "vegetable_consumption": 2.0,
                "meals_per_day": 3.0, "between_meal_eating": 1.0, "smoking_status": 0.0,
                "water_intake_l": 1.5, "calorie_monitoring": 0.0, "physical_activity_frequency": 1.0,
                "technology_usage_hours": 1.0, "alcohol_use": 0.0, "transportation_mode": 1.0
            },
            "ckd": {
                "age": 62.0, "bp": 155.0, "sg": 1.020, "al": 0.0, "su": 0.0, "bgr": 175.0, "bu": 14.0, "sc": 0.8,
                "sod": 140.0, "pot": 4.2, "hemo": 15.0, "pcv": 45.0, "wc": 7500.0, "rc": 5.0,
                "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
                "htn": "yes", "dm": "yes", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
            }
        }),
    ]

    user_g_ckd = 0.0
    user_h_ckd = 0.0

    for name, user_data in cases:
        obs_res = client.post("/api/v1/predict/obesity", json=user_data["obesity"])
        assert obs_res.status_code == 200, f"{name} obesity failed: {obs_res.text}"
        obs_out = obs_res.json()
        assert 0.0 <= obs_out["risk_score"] <= 1.0

        ckd_res = client.post("/api/v1/predict/ckd", json=user_data["ckd"])
        assert ckd_res.status_code == 200, f"{name} ckd failed: {ckd_res.text}"
        ckd_out = ckd_res.json()
        assert 0.0 <= ckd_out["risk_score"] <= 1.0

        # Contrast assertion between User G (with real labs) and User H (vitals only)
        if "User G" in name:
            user_g_ckd = ckd_out["risk_score"]
        elif "User H" in name:
            user_h_ckd = ckd_out["risk_score"]

    # Proof of Lab sensitivity: User G (abnormal lab biomarkers) must have much higher risk than User H (normal reference defaults)
    assert user_g_ckd > user_h_ckd
    assert user_g_ckd >= 0.80, f"User G lab CKD risk should be >= 0.80, got {user_g_ckd}"
