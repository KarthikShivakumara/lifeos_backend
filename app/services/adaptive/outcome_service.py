from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.adaptive import OutcomeRecord

logger = logging.getLogger("lifeos.adaptive.outcome_service")


def record_outcome(
    db: Session,
    user_id: str,
    outcome_type: str,
    outcome_value: float | None = None,
    outcome_label: str | None = None,
    measurement_date: datetime | None = None,
    source: str = "USER_REPORTED",
    verification_status: str = "UNVERIFIED",
    related_prediction_id: str | None = None,
    consent_status: str = "granted",
) -> OutcomeRecord:
    """Records follow-up outcome data, keeping USER_REPORTED and VERIFIED separate."""
    outcome = OutcomeRecord(
        user_id=user_id,
        related_prediction_id=related_prediction_id,
        outcome_type=outcome_type,
        outcome_value=outcome_value,
        outcome_label=outcome_label,
        measurement_date=measurement_date or datetime.utcnow(),
        source=source,
        verification_status=verification_status,
        consent_status=consent_status,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    logger.info(f"OutcomeRecord logged: {outcome_type} ({source}/{verification_status}) for user {user_id}")
    return outcome


def get_user_outcomes(db: Session, user_id: str, verified_only: bool = False) -> list[OutcomeRecord]:
    query = db.query(OutcomeRecord).filter(OutcomeRecord.user_id == user_id)
    if verified_only:
        query = query.filter(OutcomeRecord.verification_status == "VERIFIED")
    return query.order_by(OutcomeRecord.measurement_date.desc()).all()
