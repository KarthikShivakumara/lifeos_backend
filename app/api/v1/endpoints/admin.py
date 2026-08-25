from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.activity_log import ActivityLog
from app.models.prediction_history import PredictionHistory
from app.models.report import Report
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/dashboard")
def dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "predictions": db.query(PredictionHistory).count(),
        "reports": db.query(Report).count(),
        "activity_logs": db.query(ActivityLog).count(),
    }

