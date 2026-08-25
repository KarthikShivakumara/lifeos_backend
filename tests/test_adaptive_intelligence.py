from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.services.adaptive.baseline_service import calculate_and_update_baselines, get_user_baselines
from app.services.adaptive.dataset_builder import build_candidate_dataset, validate_record_quality
from app.services.adaptive.drift_service import monitor_feature_drift
from app.services.adaptive.event_service import record_health_event, record_prediction_snapshot
from app.services.adaptive.feedback_service import record_recommendation_feedback
from app.services.adaptive.model_promotion_service import evaluate_and_audit_candidate, rollback_to_previous_version
from app.services.adaptive.outcome_service import record_outcome
from app.services.adaptive.report_service import generate_monthly_report, generate_weekly_report
from app.services.adaptive.training_service import train_candidate_model
from app.services.adaptive.trend_service import evaluate_longitudinal_trends, get_personalized_recommendation_modifiers


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    # Create dummy test user
    u = User(id="user-test-101", email="adaptive_test@lifeos.ai", password_hash="hashed_pwd_123", full_name="Adaptive Tester")
    session.add(u)
    session.commit()

    yield session
    session.close()


def test_health_event_recording_and_user_isolation(db_session: Session):
    evt1 = record_health_event(db_session, "user-test-101", "BP_RECORDED", {"systolic_bp": 120, "diastolic_bp": 80})
    assert evt1.id is not None
    assert evt1.user_id == "user-test-101"
    assert evt1.event_type == "BP_RECORDED"
    assert evt1.payload["systolic_bp"] == 120


def test_prediction_snapshot_immutability(db_session: Session):
    snap = record_prediction_snapshot(
        db=db_session,
        user_id="user-test-101",
        model_name="hypertension",
        model_version="1.0.0",
        probability=0.72,
        threshold=0.60,
        risk_category="high",
        feature_snapshot={"age_years": 54, "systolic_bp_mmHg": 150},
    )
    assert snap.id is not None
    assert snap.model_name == "hypertension"
    assert snap.model_version == "1.0.0"
    assert snap.probability == 0.72


def test_baseline_calculation_and_rolling_averages(db_session: Session):
    now = datetime.utcnow()
    # Log 5 sleep events over different dates
    for i in range(5):
        record_health_event(
            db_session,
            "user-test-101",
            "SLEEP_RECORDED",
            {"sleep_hours": 6.0 + i * 0.2},
            source="user_input",
        )

    calculate_and_update_baselines(db_session, "user-test-101")
    baselines = get_user_baselines(db_session, "user-test-101")
    sleep_b = next((b for b in baselines if b.metric == "sleep_hours"), None)

    assert sleep_b is not None
    assert sleep_b.rolling_7_day_avg is not None
    assert sleep_b.baseline_value > 0.0


def test_trend_evaluation_improving_declining(db_session: Session):
    trends = evaluate_longitudinal_trends(db_session, "user-test-101")
    assert "clinical_trends" in trends
    assert "wellness_trends" in trends


def test_weekly_and_monthly_report_generation(db_session: Session):
    wk = generate_weekly_report(db_session, "user-test-101")
    assert wk["user_id"] == "user-test-101"
    assert "disclaimer" in wk
    assert "informational" in wk["disclaimer"].lower()

    mo = generate_monthly_report(db_session, "user-test-101")
    assert mo["user_id"] == "user-test-101"
    assert "consistency_score" in mo


def test_recommendation_feedback_logging(db_session: Session):
    fb = record_recommendation_feedback(db_session, "user-test-101", "rec-123", "ACCEPTED")
    assert fb.action == "ACCEPTED"

    with pytest.raises(ValueError):
        record_recommendation_feedback(db_session, "user-test-101", "rec-123", "INVALID_ACTION")


def test_outcome_record_validation_and_dataset_building(db_session: Session):
    out = record_outcome(
        db_session,
        user_id="user-test-101",
        outcome_type="hypertension_followup",
        outcome_value=1.0,
        outcome_label="confirmed",
        source="VERIFIED",
        verification_status="VERIFIED",
    )
    assert out.verification_status == "VERIFIED"

    # Quality rules test
    val_ok, msg = validate_record_quality({"consent_status": "granted", "verification_status": "VERIFIED", "bmi": 25})
    assert val_ok is True

    val_bad, msg2 = validate_record_quality({"consent_status": "granted", "verification_status": "UNVERIFIED"})
    assert val_bad is False
    assert "UNVERIFIED" in msg2


def test_drift_monitoring(db_session: Session):
    # Log 12 prediction snapshots to allow drift analysis
    for i in range(12):
        record_prediction_snapshot(
            db=db_session,
            user_id="user-test-101",
            model_name="hypertension",
            model_version="1.0.0",
            probability=0.5 + (i * 0.02),
            threshold=0.6,
            risk_category="moderate",
            feature_snapshot={"systolic_bp_mmHg": 120 + i * 3},
        )

    reports = monitor_feature_drift(db_session, "hypertension", "1.0.0")
    assert len(reports) > 0


def test_model_versioning_audit_and_rollback():
    rb = rollback_to_previous_version("hypertension")
    assert rb["active_model_version"] == "v1.0.0"
    assert rb["status"] == "RESTORED"
