from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ml.risk_models import engineer_risk_input, run_four_model_fusion
from app.ml.shap_adapter import compute_feature_importance
from app.models.health_assessment import HealthAssessment
from app.models.prediction_history import PredictionHistory
from app.ml.interfaces import RiskInput


@dataclass
class PredictionResult:
    feature_engineering: dict[str, float | str | None]
    model_outputs: dict[str, float]
    model_signals: list
    fused_risk: float
    heart_disease_risk: float
    diabetes_risk: float
    hypertension_risk: float
    overall_health_risk: float
    feature_importance: dict[str, float]
    explanation: str


def predict_from_assessment(assessment: HealthAssessment) -> PredictionResult:
    risk_input, feature_engineering = engineer_risk_input(
        bmi=assessment.bmi,
        systolic_bp=assessment.systolic_bp,
        diastolic_bp=assessment.diastolic_bp,
        heart_rate=assessment.heart_rate,
        spo2=assessment.spo2,
        smoking_status=assessment.smoking_status,
        alcohol_use=assessment.alcohol_use,
        exercise_frequency=assessment.exercise_frequency,
        diet_quality=assessment.diet_quality,
        stress_level=assessment.stress_level,
        sleep_hours=assessment.sleep_hours,
    )
    model_outputs, fused_risk, model_signals = run_four_model_fusion(risk_input)
    heart = model_outputs["heart-risk-model"]
    diabetes = model_outputs["diabetes-risk-model"]
    hypertension = model_outputs["hypertension-risk-model"]
    overall = model_outputs["overall-health-risk-model"]
    feature_importance = compute_feature_importance(risk_input)
    explanation = (
        "Risk is fused from four specialist models covering heart disease, diabetes, hypertension, and overall health. "
        f"Main feature drivers: {', '.join(list(feature_importance.keys())[:4])}."
    )
    return PredictionResult(
        feature_engineering=feature_engineering,
        model_outputs=model_outputs,
        model_signals=model_signals,
        fused_risk=fused_risk,
        heart_disease_risk=heart,
        diabetes_risk=diabetes,
        hypertension_risk=hypertension,
        overall_health_risk=overall,
        feature_importance=feature_importance,
        explanation=explanation,
    )


def create_prediction(db: Session, user_id: str, assessment: HealthAssessment, result: PredictionResult | None = None) -> PredictionHistory:
    result = result or predict_from_assessment(assessment)
    prediction = PredictionHistory(
        user_id=user_id,
        assessment_id=assessment.id,
        model_name="four-model-fusion-v1",
        heart_disease_risk=result.heart_disease_risk,
        diabetes_risk=result.diabetes_risk,
        hypertension_risk=result.hypertension_risk,
        overall_health_risk=result.overall_health_risk,
        explanation=result.explanation,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
