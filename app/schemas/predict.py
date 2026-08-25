from __future__ import annotations

from pydantic import BaseModel

from app.schemas.assessment import HealthAssessmentCreate


class PredictionDetailRead(BaseModel):
    heart: float
    diabetes: float
    hypertension: float
    obesity: float


class PredictResponse(BaseModel):
    overall_health_score: float
    overall_risk: str
    predictions: PredictionDetailRead
    priority: list[str]
    recommendations: list[str]
    feature_engineering: dict[str, float]
    health_twin: dict
    assessment_id: str | None = None

