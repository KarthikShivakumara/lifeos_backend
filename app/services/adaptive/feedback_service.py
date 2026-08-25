from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.adaptive import RecommendationFeedback

logger = logging.getLogger("lifeos.adaptive.feedback_service")


def record_recommendation_feedback(
    db: Session, user_id: str, recommendation_id: str, action: str
) -> RecommendationFeedback:
    """Records recommendation feedback (ACCEPTED, DISMISSED, COMPLETED, NOT_RELEVANT, SNOOZED)."""
    valid_actions = {"ACCEPTED", "DISMISSED", "COMPLETED", "NOT_RELEVANT", "SNOOZED"}
    if action not in valid_actions:
        raise ValueError(f"Invalid feedback action '{action}'. Must be one of {valid_actions}")

    feedback = RecommendationFeedback(
        user_id=user_id,
        recommendation_id=recommendation_id,
        action=action,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    logger.info(f"RecommendationFeedback recorded: {recommendation_id} -> {action} for user {user_id}")
    return feedback


def get_user_feedback(db: Session, user_id: str) -> list[RecommendationFeedback]:
    return (
        db.query(RecommendationFeedback)
        .filter(RecommendationFeedback.user_id == user_id)
        .order_by(RecommendationFeedback.timestamp.desc())
        .all()
    )
