from __future__ import annotations

from dataclasses import dataclass

from app.ml.interfaces import RiskInput


@dataclass
class ModelSignal:
    name: str
    risk: float
    rationale: str


def clamp(value: float) -> float:
    return max(0.0, min(100.0, round(value, 1)))


def score_from_lifestyle(value: str | None, healthy_terms: set[str], inverse: bool = False) -> float:
    if not value:
        return 60.0
    normalized = value.lower()
    is_healthy = any(term in normalized for term in healthy_terms)
    base = 85.0 if is_healthy else 45.0
    return 100.0 - base if inverse else base


def engineer_risk_input(
    *,
    bmi: float | None,
    systolic_bp: int | None,
    diastolic_bp: int | None,
    heart_rate: int | None,
    spo2: int | None,
    smoking_status: str | None,
    alcohol_use: str | None,
    exercise_frequency: str | None,
    diet_quality: str | None,
    stress_level: str | None,
    sleep_hours: float | None,
) -> tuple[RiskInput, dict[str, float | str | None]]:
    risk_input = RiskInput(
        bmi=bmi,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        heart_rate=heart_rate,
        spo2=spo2,
        smoking_status=smoking_status,
        alcohol_use=alcohol_use,
        exercise_frequency=exercise_frequency,
        diet_quality=diet_quality,
        stress_level=stress_level,
        sleep_hours=sleep_hours,
    )
    engineered = {
        "BMI": round(bmi, 2) if bmi is not None else None,
        "Pulse Pressure": (systolic_bp - diastolic_bp) if systolic_bp is not None and diastolic_bp is not None else None,
        "Sleep Debt": round(max(0.0, 7.0 - (sleep_hours or 7.0)), 2),
        "Activity Score": score_from_lifestyle(exercise_frequency, {"daily", "regular", "5x", "4x", "3x"}),
        "Diet Score": score_from_lifestyle(diet_quality, {"balanced", "healthy", "good"}),
        "Stress Score": 100.0 if stress_level and "low" in stress_level.lower() else 55.0 if stress_level else 50.0,
    }
    return risk_input, engineered


class HeartRiskModel:
    name = "heart-risk-model"

    def predict(self, data: RiskInput) -> ModelSignal:
        bmi = data.bmi or 24.0
        systolic = data.systolic_bp or 120
        smoking_penalty = 18.0 if data.smoking_status and data.smoking_status.lower() not in {"never", "no", "none"} else 0.0
        alcohol_penalty = 8.0 if data.alcohol_use and data.alcohol_use.lower() not in {"never", "no", "none"} else 0.0
        stress_penalty = 14.0 if data.stress_level and "high" in data.stress_level.lower() else 6.0 if data.stress_level else 8.0
        risk = 20 + max(0, bmi - 22) * 1.6 + max(0, systolic - 120) * 0.35 + smoking_penalty + alcohol_penalty + stress_penalty
        return ModelSignal(self.name, clamp(risk), "Heart risk rises with BMI, blood pressure, smoking, alcohol use, and stress.")


class DiabetesRiskModel:
    name = "diabetes-risk-model"

    def predict(self, data: RiskInput) -> ModelSignal:
        bmi = data.bmi or 24.0
        sleep_hours = data.sleep_hours or 7.0
        diet_penalty = 14.0 if data.diet_quality and any(term in data.diet_quality.lower() for term in {"fried", "sugary", "poor", "processed"}) else 4.0
        activity_penalty = 12.0 if data.exercise_frequency and data.exercise_frequency.lower() not in {"daily", "regular", "5x", "4x", "3x"} else 0.0
        risk = 18 + max(0, bmi - 23) * 1.9 + max(0, 7.0 - sleep_hours) * 2.2 + diet_penalty + activity_penalty
        return ModelSignal(self.name, clamp(risk), "Diabetes risk is influenced by BMI, sleep duration, diet quality, and activity level.")


class HypertensionRiskModel:
    name = "hypertension-risk-model"

    def predict(self, data: RiskInput) -> ModelSignal:
        systolic = data.systolic_bp or 120
        diastolic = data.diastolic_bp or 80
        stress_penalty = 16.0 if data.stress_level and "high" in data.stress_level.lower() else 6.0 if data.stress_level else 8.0
        alcohol_penalty = 10.0 if data.alcohol_use and data.alcohol_use.lower() not in {"never", "no", "none"} else 0.0
        risk = 22 + max(0, systolic - 118) * 0.55 + max(0, diastolic - 78) * 0.8 + stress_penalty + alcohol_penalty
        return ModelSignal(self.name, clamp(risk), "Hypertension risk is driven by systolic/diastolic pressure, stress, and alcohol use.")


class OverallHealthRiskModel:
    name = "overall-health-risk-model"

    def predict(self, data: RiskInput) -> ModelSignal:
        bmi = data.bmi or 24.0
        hr = data.heart_rate or 72
        spo2 = data.spo2 or 98
        sleep_hours = data.sleep_hours or 7.0
        stress_penalty = 12.0 if data.stress_level and "high" in data.stress_level.lower() else 4.0 if data.stress_level else 6.0
        activity_penalty = 8.0 if data.exercise_frequency and data.exercise_frequency.lower() not in {"daily", "regular", "5x", "4x", "3x"} else 0.0
        risk = 16 + max(0, bmi - 22) * 1.2 + max(0, 96 - spo2) * 1.4 + max(0, hr - 78) * 0.4 + max(0, 7.0 - sleep_hours) * 1.8 + stress_penalty + activity_penalty
        return ModelSignal(self.name, clamp(risk), "Overall health risk blends vital signs, sleep, stress, and lifestyle signals.")


def run_four_model_fusion(data: RiskInput) -> tuple[dict[str, float], float, list[ModelSignal]]:
    models = [
        HeartRiskModel(),
        DiabetesRiskModel(),
        HypertensionRiskModel(),
        OverallHealthRiskModel(),
    ]
    signals = [model.predict(data) for model in models]
    model_scores = {signal.name: signal.risk for signal in signals}
    fused = clamp(
        (model_scores["heart-risk-model"] * 0.30)
        + (model_scores["diabetes-risk-model"] * 0.25)
        + (model_scores["hypertension-risk-model"] * 0.25)
        + (model_scores["overall-health-risk-model"] * 0.20)
    )
    return model_scores, fused, signals
