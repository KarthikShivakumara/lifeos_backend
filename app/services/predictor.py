from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ml.model_store import load_model
from app.ml.preprocessing import preprocess_request
from app.models.prediction_history import PredictionHistory
from app.models.recommendation import Recommendation
from app.schemas.assessment import HealthAssessmentCreate
from app.services.assessment import create_assessment, upsert_profile
from app.services.activity import log_activity
from app.services.twin import build_health_twin


@dataclass
class PredictResponsePayload:
    overall_health_score: float
    overall_risk: str
    predictions: dict[str, float]
    priority: list[str]
    recommendations: list[str]
    feature_engineering: dict[str, float]
    health_twin: dict
    assessment_id: str | None


def risk_band(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 45:
        return "Moderate"
    return "Low"


def calculate_overall_score(predictions: dict[str, float]) -> float:
    average_risk = sum(predictions.values()) / max(1, len(predictions))
    return round(max(0.0, min(100.0, 100.0 - average_risk)), 1)


def generate_rules(predictions: dict[str, float]) -> tuple[list[str], list[str]]:
    priority_items = sorted(predictions.items(), key=lambda item: item[1], reverse=True)
    priority = [name.capitalize() for name, score in priority_items if score >= 50]
    recommendations: list[str] = []
    if predictions.get("hypertension", 0) > 70:
        recommendations.extend(["Reduce salt", "Monitor BP daily", "Exercise regularly"])
    if predictions.get("diabetes", 0) > 70:
        recommendations.extend(["Reduce sugar", "Walk 30 mins", "Check HbA1c"])
    if predictions.get("obesity", 0) > 60:
        recommendations.extend(["Weight loss goal", "Cardio 4x/week", "Protein-rich diet"])
    if predictions.get("heart", 0) > 60:
        recommendations.extend(["Lower saturated fat", "Improve sleep", "Stress reduction"])
    if not recommendations:
        recommendations = ["Maintain healthy habits", "Stay active", "Keep regular checkups"]
    return priority or ["Heart", "Diabetes", "Hypertension", "Obesity"], recommendations


def save_prediction_history(db: Session, user_id: str, assessment_id: str, predictions: dict[str, float], overall_score: float) -> PredictionHistory:
    prediction = PredictionHistory(
        user_id=user_id,
        assessment_id=assessment_id,
        model_name="mvp-four-model-fusion",
        heart_disease_risk=predictions["heart"],
        diabetes_risk=predictions["diabetes"],
        hypertension_risk=predictions["hypertension"],
        overall_health_risk=overall_score,
        explanation="MVP fused prediction generated from heart, diabetes, hypertension, and obesity models.",
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def save_recommendations(db: Session, user_id: str, assessment_id: str, items: list[str]) -> list[Recommendation]:
    saved: list[Recommendation] = []
    for item in items:
        priority = "high" if item in {"Reduce salt", "Reduce sugar", "Weight loss goal", "Monitor BP daily"} else "medium"
        rec = Recommendation(
            user_id=user_id,
            assessment_id=assessment_id,
            category="MVP",
            title=item,
            description=item,
            priority=priority,
        )
        db.add(rec)
        saved.append(rec)
    db.commit()
    for rec in saved:
        db.refresh(rec)
    return saved


def run_predict_pipeline(db: Session, user_id: str, payload: HealthAssessmentCreate) -> PredictResponsePayload:
    upsert_profile(db, user_id, payload)
    assessment = create_assessment(db, user_id, payload)
    log_activity(db, user_id, "assessment_created", "health_assessment", assessment.id)

    preprocessed = preprocess_request(payload)
    heart_model = load_model("heart")
    diabetes_model = load_model("diabetes")
    hypertension_model = load_model("hypertension")
    obesity_model = load_model("obesity")

    predictions = {
        "heart": heart_model.predict_score(preprocessed.features),
        "diabetes": diabetes_model.predict_score(preprocessed.features),
        "hypertension": hypertension_model.predict_score(preprocessed.features),
        "obesity": obesity_model.predict_score(preprocessed.features),
    }
    overall_health_score = calculate_overall_score(predictions)
    overall_risk = risk_band(overall_health_score)
    priority, recommendations_text = generate_rules(predictions)

    prediction_record = save_prediction_history(db, user_id, assessment.id, predictions, overall_health_score)
    log_activity(db, user_id, "prediction_generated", "prediction", prediction_record.id)

    recommendation_records = save_recommendations(db, user_id, assessment.id, recommendations_text)
    if recommendation_records:
        log_activity(db, user_id, "recommendations_generated", "recommendation", recommendation_records[0].id, f"{len(recommendation_records)} recommendations created")

    twin = build_health_twin(db, user_id)
    return PredictResponsePayload(
        overall_health_score=overall_health_score,
        overall_risk=overall_risk,
        predictions=predictions,
        priority=priority,
        recommendations=recommendations_text,
        feature_engineering=preprocessed.features,
        health_twin=twin,
        assessment_id=assessment.id,
    )
