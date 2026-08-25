from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services.reports import create_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportRead)
def create(payload: ReportCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_report(db, current_user.id, payload.report_type, payload.title, payload.summary)


@router.get("", response_model=list[ReportRead])
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Report).filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()

