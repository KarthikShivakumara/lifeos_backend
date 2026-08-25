from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.assessment import HealthAssessmentCreate
from app.schemas.predict import PredictResponse, PredictionDetailRead
from app.services.predictor import run_predict_pipeline

router = APIRouter(tags=["MVP Prediction"])


@router.post("/predict", response_model=PredictResponse)
def predict(
    payload: HealthAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = run_predict_pipeline(db, current_user.id, payload)
    return PredictResponse(
        overall_health_score=result.overall_health_score,
        overall_risk=result.overall_risk,
        predictions=PredictionDetailRead(**result.predictions),
        priority=result.priority,
        recommendations=result.recommendations,
        feature_engineering=result.feature_engineering,
        health_twin=result.health_twin,
        assessment_id=result.assessment_id,
    )
