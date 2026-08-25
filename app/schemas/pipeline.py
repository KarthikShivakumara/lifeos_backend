from pydantic import BaseModel

from app.schemas.assessment import HealthAssessmentRead, HealthTwinRead
from app.schemas.prediction import PredictionRead
from app.schemas.recommendation import RecommendationRead


class ModelSignalRead(BaseModel):
    model_name: str
    risk_score: float
    rationale: str


class PipelineResponse(BaseModel):
    assessment: HealthAssessmentRead
    feature_engineering: dict[str, float | str | None]
    model_signals: list[ModelSignalRead]
    fused_risk: float
    feature_importance: dict[str, float]
    prediction: PredictionRead
    recommendations: list[RecommendationRead]
    health_twin: HealthTwinRead
