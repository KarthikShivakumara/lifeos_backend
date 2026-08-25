from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.health_assessment import HealthAssessment
from app.models.prediction_history import PredictionHistory
from app.models.user import User
from app.schemas.prediction import PredictionResponse, PredictionRead
from app.services.prediction import create_prediction, predict_from_assessment

router = APIRouter(prefix="/predictions", tags=["Prediction"])


@router.post("/assessments/{assessment_id}", response_model=PredictionResponse)
def predict(assessment_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessment = db.query(HealthAssessment).filter(HealthAssessment.id == assessment_id, HealthAssessment.user_id == current_user.id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    prediction = create_prediction(db, current_user.id, assessment)
    result = predict_from_assessment(assessment)
    return PredictionResponse(prediction=prediction, feature_importance=result.feature_importance)


@router.get("", response_model=list[PredictionRead])
def list_predictions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(PredictionHistory).filter_by(user_id=current_user.id).order_by(PredictionHistory.created_at.desc()).all()

