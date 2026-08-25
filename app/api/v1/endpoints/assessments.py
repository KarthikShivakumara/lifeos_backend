from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.health_assessment import HealthAssessment
from app.models.user import User
from app.schemas.assessment import HealthAssessmentCreate, HealthAssessmentRead
from app.services.activity import log_activity
from app.services.assessment import create_assessment, upsert_profile

router = APIRouter(prefix="/assessments", tags=["Assessment"])


@router.post("", response_model=HealthAssessmentRead)
def create(payload: HealthAssessmentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    upsert_profile(db, current_user.id, payload)
    assessment = create_assessment(db, current_user.id, payload)
    log_activity(db, current_user.id, "assessment_created", "health_assessment", assessment.id)
    return assessment


@router.get("", response_model=list[HealthAssessmentRead])
def list_assessments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(HealthAssessment).filter_by(user_id=current_user.id).order_by(HealthAssessment.created_at.desc()).all()
