from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.prediction_history import PredictionHistory
from app.models.user import User
from app.schemas.coach import CoachMessage, CoachReply
from app.services.coach import answer_health_query

router = APIRouter(prefix="/coach", tags=["AI Coach"])


@router.post("/chat", response_model=CoachReply)
def chat(payload: CoachMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest = db.query(PredictionHistory).filter(PredictionHistory.user_id == current_user.id).order_by(PredictionHistory.created_at.desc()).first()
    context = payload.context or {}
    if latest:
        context.setdefault("overall_health_risk", latest.overall_health_risk)
        context.setdefault("explanation", latest.explanation)
    return answer_health_query(payload.message, context)

