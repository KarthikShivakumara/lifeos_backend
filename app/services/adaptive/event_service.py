from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.models.adaptive import HealthEvent, PredictionSnapshot
from app.schemas.adaptive import HealthEventCreate, PredictionSnapshotCreate

logger = logging.getLogger("lifeos.adaptive.event_service")


def record_health_event(
    db: Session,
    user_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    source: str = "user_input",
    model_version: str | None = None,
    consent_status: str = "granted",
) -> HealthEvent:
    """Logs a user health event into the longitudinal event stream."""
    event = HealthEvent(
        user_id=user_id,
        event_type=event_type,
        payload=payload or {},
        source=source,
        model_version=model_version,
        consent_status=consent_status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"HealthEvent recorded: {event_type} for user {user_id}")
    return event


def record_prediction_snapshot(
    db: Session,
    user_id: str,
    model_name: str,
    model_version: str,
    probability: float,
    threshold: float,
    risk_category: str,
    feature_snapshot: dict[str, Any] | None = None,
    assessment_id: str | None = None,
) -> PredictionSnapshot:
    """Preserves an immutable snapshot of a production model prediction."""
    snapshot = PredictionSnapshot(
        user_id=user_id,
        assessment_id=assessment_id,
        model_name=model_name,
        model_version=model_version,
        probability=probability,
        threshold=threshold,
        risk_category=risk_category,
        feature_snapshot=feature_snapshot or {},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    logger.info(f"PredictionSnapshot stored: {model_name} v{model_version} ({risk_category}) for user {user_id}")
    return snapshot


def get_user_events(db: Session, user_id: str, limit: int = 100, event_type: str | None = None) -> list[HealthEvent]:
    query = db.query(HealthEvent).filter(HealthEvent.user_id == user_id)
    if event_type:
        query = query.filter(HealthEvent.event_type == event_type)
    return query.order_by(HealthEvent.timestamp.desc()).limit(limit).all()


def get_user_prediction_snapshots(db: Session, user_id: str, model_name: str | None = None) -> list[PredictionSnapshot]:
    query = db.query(PredictionSnapshot).filter(PredictionSnapshot.user_id == user_id)
    if model_name:
        query = query.filter(PredictionSnapshot.model_name == model_name)
    return query.order_by(PredictionSnapshot.timestamp.desc()).all()
