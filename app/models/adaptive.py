from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class HealthEvent(Base):
    __tablename__ = "health_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(64), default="user_input", nullable=False)
    payload = Column(JSON, nullable=True)
    model_version = Column(String(64), nullable=True)
    consent_status = Column(String(32), default="granted", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="health_events")

    __table_args__ = (
        Index("idx_health_events_user_type", "user_id", "event_type"),
        Index("idx_health_events_user_time", "user_id", "timestamp"),
    )


class PredictionSnapshot(Base):
    __tablename__ = "prediction_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(64), nullable=True, index=True)
    model_name = Column(String(64), nullable=False, index=True)
    model_version = Column(String(64), nullable=False)
    probability = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    risk_category = Column(String(32), nullable=False)
    feature_snapshot = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", backref="prediction_snapshots")

    __table_args__ = (
        Index("idx_prediction_snapshots_user_model", "user_id", "model_name"),
    )


class UserBaseline(Base):
    __tablename__ = "user_baselines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric = Column(String(64), nullable=False, index=True)
    baseline_value = Column(Float, nullable=False)
    rolling_7_day_avg = Column(Float, nullable=True)
    rolling_30_day_avg = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    std_deviation = Column(Float, nullable=True)
    current_deviation = Column(Float, nullable=True)
    trend = Column(String(32), default="INSUFFICIENT_DATA", nullable=False)
    consistency_score = Column(Float, default=1.0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="user_baselines")

    __table_args__ = (
        Index("idx_user_baselines_user_metric", "user_id", "metric", unique=True),
    )


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(String(128), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # ACCEPTED, DISMISSED, COMPLETED, NOT_RELEVANT, SNOOZED
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="recommendation_feedback")


class OutcomeRecord(Base):
    __tablename__ = "outcome_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_prediction_id = Column(String(36), nullable=True)
    outcome_type = Column(String(64), nullable=False)  # LAB_RESULT, CLINICAL_FOLLOWUP, WEIGHT_CHANGE, etc.
    outcome_value = Column(Float, nullable=True)
    outcome_label = Column(String(64), nullable=True)
    measurement_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(32), default="USER_REPORTED", nullable=False)  # USER_REPORTED vs VERIFIED
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)  # VERIFIED vs UNVERIFIED
    consent_status = Column(String(32), default="granted", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="outcome_records")


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(64), nullable=False, index=True)
    model_version = Column(String(64), nullable=False)
    feature = Column(String(64), nullable=False)
    baseline_mean = Column(Float, nullable=True)
    current_mean = Column(Float, nullable=True)
    drift_score = Column(Float, nullable=False)
    severity = Column(String(32), default="LOW", nullable=False)  # LOW, MODERATE, HIGH
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
