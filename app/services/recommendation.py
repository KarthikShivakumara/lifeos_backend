from sqlalchemy.orm import Session

from app.models.prediction_history import PredictionHistory
from app.models.recommendation import Recommendation


def generate_recommendations(db: Session, user_id: str, prediction: PredictionHistory) -> list[Recommendation]:
    items: list[tuple[str, str, str, str]] = []
    if prediction.hypertension_risk >= 60:
        items.append(("Blood Pressure", "Monitor blood pressure", "Track BP daily and reduce sodium intake.", "high"))
    if prediction.diabetes_risk >= 55:
        items.append(("Glucose", "Stabilize glucose risk", "Build meals around fiber, protein, and lower glycemic foods.", "high"))
    if prediction.heart_disease_risk >= 50:
        items.append(("Cardio", "Support heart health", "Aim for 150 minutes of moderate activity per week.", "medium"))
    if prediction.overall_health_risk >= 65:
        items.append(("Recovery", "Prioritize sleep", "Protect 7 to 9 hours of sleep and maintain a fixed bedtime.", "high"))
    if not items:
        items.append(("Wellness", "Maintain current habits", "Continue balanced nutrition, movement, hydration, and routine checkups.", "medium"))

    saved: list[Recommendation] = []
    for category, title, description, priority in items:
        rec = Recommendation(user_id=user_id, category=category, title=title, description=description, priority=priority, assessment_id=prediction.assessment_id)
        db.add(rec)
        saved.append(rec)
    db.commit()
    for rec in saved:
        db.refresh(rec)
    return saved

