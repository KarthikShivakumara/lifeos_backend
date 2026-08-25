from app.ml.interfaces import RiskInput


def compute_feature_importance(data: RiskInput) -> dict[str, float]:
    bmi = data.bmi or 24.0
    systolic = data.systolic_bp or 120
    stress = data.stress_level or "medium"
    sleep_hours = data.sleep_hours or 7.0
    smoking = data.smoking_status or "never"

    return {
        "BMI": round(min(18.0, abs(bmi - 22) * 1.6), 2),
        "Blood Pressure": round(min(16.0, max(0, systolic - 118) * 0.4), 2),
        "Stress": 12.0 if "high" in stress.lower() else 5.0,
        "Sleep": round(min(12.0, max(0, 7.0 - sleep_hours) * 2.5), 2),
        "Smoking": 18.0 if smoking.lower() not in {"never", "no", "none"} else 0.0,
    }

