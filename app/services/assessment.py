from sqlalchemy.orm import Session

from app.models.health_assessment import HealthAssessment
from app.models.lifestyle_record import LifestyleRecord
from app.models.profile import Profile
from app.schemas.assessment import HealthAssessmentCreate


def calculate_bmi(height_cm: float | None, weight_kg: float | None) -> float | None:
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100.0
    if height_m <= 0:
        return None
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 2)


def score_from_lifestyle(value: str | None, healthy_terms: set[str], inverse: bool = False) -> float:
    if not value:
        return 60.0
    normalized = value.lower()
    is_healthy = any(term in normalized for term in healthy_terms)
    base = 85.0 if is_healthy else 45.0
    return 100.0 - base if inverse else base


def create_assessment(db: Session, user_id: str, payload: HealthAssessmentCreate) -> HealthAssessment:
    bmi = calculate_bmi(payload.height_cm, payload.weight_kg)
    assessment = HealthAssessment(
        user_id=user_id,
        bmi=bmi,
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        smoking_status=payload.smoking_status,
        alcohol_use=payload.alcohol_use,
        exercise_frequency=payload.exercise_frequency,
        diet_quality=payload.diet_quality,
        stress_level=payload.stress_level,
        sleep_hours=payload.sleep_hours,
        notes=payload.notes,
    )
    db.add(assessment)
    db.flush()
    lifestyle = LifestyleRecord(
        assessment_id=assessment.id,
        activity_score=score_from_lifestyle(payload.exercise_frequency, {"daily", "regular", "5x", "4x", "3x"}),
        diet_score=score_from_lifestyle(payload.diet_quality, {"balanced", "healthy", "good"}),
        sleep_score=100.0 if (payload.sleep_hours or 0) >= 7 else 60.0 if payload.sleep_hours else 50.0,
        stress_score=100.0 if payload.stress_level and "low" in payload.stress_level.lower() else 55.0,
        habits_summary="Lifestyle record generated from current assessment inputs.",
    )
    db.add(lifestyle)
    db.commit()
    db.refresh(assessment)
    return assessment


def upsert_profile(db: Session, user_id: str, payload: HealthAssessmentCreate) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
    profile.age = payload.age
    profile.gender = payload.gender
    profile.height_cm = payload.height_cm
    profile.weight_kg = payload.weight_kg
    db.commit()
    db.refresh(profile)
    return profile
