from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.health_assessment import HealthAssessment
from app.models.prediction_history import PredictionHistory
from app.models.profile import Profile


def build_health_twin(db: Session, user_id: str) -> dict:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    last_assessment = db.query(HealthAssessment).filter(HealthAssessment.user_id == user_id).order_by(HealthAssessment.created_at.desc()).first()
    last_prediction = db.query(PredictionHistory).filter(PredictionHistory.user_id == user_id).order_by(PredictionHistory.created_at.desc()).first()

    health_score = 100.0
    lifestyle_score = 78.0
    wellness_score = 84.0
    summary = "Insufficient assessment data for a rich health twin."
    if last_prediction:
        health_score = round(100 - last_prediction.overall_health_risk, 1)
        wellness_score = round(max(35.0, health_score - 4), 1)
        summary = "Health twin updated from the latest assessment and prediction."
    if last_assessment:
        if last_assessment.bmi and last_assessment.bmi >= 30:
            lifestyle_score -= 8
        if last_assessment.sleep_hours and last_assessment.sleep_hours < 6:
            lifestyle_score -= 7
    return {
        "user_id": user_id,
        "profile": {
            "age": profile.age if profile else None,
            "gender": profile.gender if profile else None,
        },
        "health_score": max(0.0, round(health_score, 1)),
        "lifestyle_score": max(0.0, round(lifestyle_score, 1)),
        "wellness_score": max(0.0, round(wellness_score, 1)),
        "risk_band": "high" if health_score < 55 else "moderate" if health_score < 75 else "low",
        "summary": summary,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

