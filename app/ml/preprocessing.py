from __future__ import annotations

from dataclasses import dataclass

from app.schemas.assessment import HealthAssessmentCreate
from app.ml.mvp_models import normalize_yes_no, numeric


@dataclass
class PreprocessedInput:
    raw: dict[str, object | None]
    features: dict[str, float]
    bmi: float


def calculate_bmi(height_cm: float | None, weight_kg: float | None, fallback: float | None = None) -> float:
    if fallback is not None:
        return round(fallback, 2)
    if not height_cm or not weight_kg:
        return 0.0
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m * height_m), 2)


def encode_exercise(value: object | None) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().lower()
    if text in {"daily", "regular", "high", "5", "5x", "5x/week"}:
        return 1.0
    if text in {"4", "4x", "4x/week", "moderate"}:
        return 0.8
    if text in {"3", "3x", "3x/week"}:
        return 0.6
    if text in {"2", "2x", "2x/week", "light"}:
        return 0.4
    if text in {"1", "1x", "1x/week", "low"}:
        return 0.2
    return numeric(value, 0.0)


def encode_smoking(value: object | None) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().lower()
    return 0.0 if text in {"0", "no", "never", "none", "n"} else 1.0


def encode_gender(value: object | None) -> float:
    text = str(value).strip().lower() if value is not None else ""
    if text.startswith("m"):
        return 1.0
    if text.startswith("f"):
        return 0.0
    return 0.5


def diet_numeric(value: object | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if text in {"healthy", "balanced", "good", "high"}:
        return 1.0
    if text in {"average", "medium", "moderate"}:
        return 0.6
    if text in {"poor", "low", "unhealthy"}:
        return 0.2
    try:
        return float(text)
    except ValueError:
        return 0.0


def preprocess_request(payload: HealthAssessmentCreate) -> PreprocessedInput:
    bmi = calculate_bmi(payload.height_cm, payload.weight_kg, payload.bmi)
    raw = payload.model_dump()
    features = {
        "age": numeric(payload.age, 45.0),
        "gender": encode_gender(payload.gender),
        "bmi": bmi,
        "glucose": numeric(payload.glucose, 110.0),
        "systolic_bp": numeric(payload.systolic_bp, 120.0),
        "diastolic_bp": numeric(payload.diastolic_bp, 80.0),
        "cholesterol": numeric(payload.cholesterol, 180.0),
        "smoking": encode_smoking(payload.smoking_status),
        "alcohol": encode_smoking(payload.alcohol_use),
        "exercise": encode_exercise(payload.exercise_frequency),
        "sleep_hours": numeric(payload.sleep_hours, 7.0),
        "stress": 1.0 if payload.stress_level and "high" in payload.stress_level.lower() else 0.5 if payload.stress_level else 0.0,
        "depression_score": numeric(payload.depression_score, 20.0),
        "family_history_diabetes": normalize_yes_no(payload.family_history_diabetes),
        "family_history_heart_disease": normalize_yes_no(payload.family_history_heart_disease),
        "family_history_stroke": normalize_yes_no(payload.family_history_stroke),
        "water_intake_l": numeric(payload.water_intake_l, 2.0),
        "heart_rate": numeric(payload.heart_rate, 72.0),
        "spo2": numeric(payload.spo2, 98.0),
        "diet": diet_numeric(payload.diet_quality),
    }
    return PreprocessedInput(raw=raw, features=features, bmi=bmi)
