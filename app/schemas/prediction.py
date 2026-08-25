from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class PredictionRead(ORMModel):
    id: str
    user_id: str
    assessment_id: str | None
    model_name: str
    heart_disease_risk: float
    diabetes_risk: float
    hypertension_risk: float
    overall_health_risk: float
    explanation: str | None
    created_at: datetime


class PredictionResponse(BaseModel):
    prediction: PredictionRead
    feature_importance: dict[str, float]
