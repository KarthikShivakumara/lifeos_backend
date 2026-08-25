from sqlalchemy.orm import Session

from app.models.report import Report


def create_report(db: Session, user_id: str, report_type: str, title: str, summary: str) -> Report:
    report = Report(user_id=user_id, report_type=report_type, title=title, summary=summary)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

