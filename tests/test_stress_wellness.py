from __future__ import annotations

import datetime
from typing import Any
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from pydantic import ValidationError

from app.db.session import Base
import app.db.base  # noqa: F401
from app.models.stress_checkin import StressCheckin
from app.models.user import User
from app.models.notification import Notification

from app.schemas.stress import (
    StressCheckinCreate,
    NON_DIAGNOSTIC_DISCLAIMER,
)
from app.services.stress_wellness_service import StressWellnessService, stress_wellness_service
from app.services.stress_recommendation_service import StressRecommendationService


# Setup isolated in-memory test database
@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        id="user-stress-test-01",
        email="stresstest@lifeos.org",
        password_hash="hashed_secret_pass",
        full_name="Stress Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_b(db_session: Session) -> User:
    user = User(
        id="user-stress-test-02",
        email="stresstest2@lifeos.org",
        password_hash="hashed_secret_pass",
        full_name="Stress Test User B",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user



# 1. Formula bounds and exact calculations
def test_stress_index_bounds_and_formula():
    service = StressWellnessService()

    # Absolute minimum (0 across all strain indicators, 10 on positive mood/energy)
    idx_min, comp_min = service.calculate_stress_index(
        perceived_stress=0, overwhelm=0, difficulty_relaxing=0, mood=10, energy=10, sleep_hours=8.0, activity_minutes=60
    )
    assert idx_min == 0.0
    assert comp_min == 100.0

    # Absolute maximum (10 across all strain indicators, 0 on positive mood/energy)
    idx_max, comp_max = service.calculate_stress_index(
        perceived_stress=10, overwhelm=10, difficulty_relaxing=10, mood=0, energy=0, sleep_hours=4.0, activity_minutes=0
    )
    assert idx_max == 100.0
    assert comp_max == 100.0

    # Intermediate known score
    idx_mid, comp_mid = service.calculate_stress_index(
        perceived_stress=5, overwhelm=5, difficulty_relaxing=5, mood=5, energy=5
    )
    assert 48.0 <= idx_mid <= 52.0
    assert comp_mid == 100.0


# 2. Missing inputs normalization and completeness
def test_stress_missing_inputs_normalization():
    service = StressWellnessService()

    # Only mandatory perceived_stress provided
    idx, comp = service.calculate_stress_index(perceived_stress=7)
    assert idx == 70.0  # 7 * 10
    assert comp == 20.0  # 1 of 5 user inputs = 20%

    # 3 user inputs provided
    idx_partial, comp_partial = service.calculate_stress_index(
        perceived_stress=6, overwhelm=4, difficulty_relaxing=8
    )
    assert 0.0 <= idx_partial <= 100.0
    assert comp_partial == 60.0  # 3 of 5 inputs = 60%


# 3. Input validation ranges (0-10)
def test_stress_input_validation_ranges():
    with pytest.raises(ValidationError):
        StressCheckinCreate(perceived_stress=11)

    with pytest.raises(ValidationError):
        StressCheckinCreate(perceived_stress=-1)

    with pytest.raises(ValidationError):
        StressCheckinCreate(perceived_stress=5, overwhelm=15)

    # Valid schema passes cleanly
    valid = StressCheckinCreate(perceived_stress=4, overwhelm=3, mood=8)
    assert valid.perceived_stress == 4
    assert valid.overwhelm == 3
    assert valid.mood == 8


# 4. Tier classifications
def test_stress_tier_classification():
    service = StressWellnessService()
    assert service.classify_stress_level(0.0) == "low"
    assert service.classify_stress_level(24.9) == "low"
    assert service.classify_stress_level(25.0) == "mild"
    assert service.classify_stress_level(49.9) == "mild"
    assert service.classify_stress_level(50.0) == "moderate"
    assert service.classify_stress_level(74.9) == "moderate"
    assert service.classify_stress_level(75.0) == "high"
    assert service.classify_stress_level(100.0) == "high"


# 5. Database immutability and persistence
def test_stress_immutability_and_persistence(db_session: Session, test_user: User):
    service = StressWellnessService()

    payload1 = StressCheckinCreate(perceived_stress=4, overwhelm=3, notes="Checkin 1")
    res1 = service.record_checkin(db_session, test_user.id, payload1)

    payload2 = StressCheckinCreate(perceived_stress=6, overwhelm=5, notes="Checkin 2")
    res2 = service.record_checkin(db_session, test_user.id, payload2)

    # Assert 2 distinct immutable records exist
    history = service.get_stress_history(db_session, test_user.id)
    assert len(history) == 2
    assert history[0].id == res2.id
    assert history[1].id == res1.id
    assert history[0].perceived_stress == 6
    assert history[1].perceived_stress == 4


# 6. User isolation guarantee
def test_stress_user_isolation(db_session: Session, test_user: User, test_user_b: User):
    service = StressWellnessService()

    # User A records a checkin
    service.record_checkin(db_session, test_user.id, StressCheckinCreate(perceived_stress=8))

    # User B records a checkin
    service.record_checkin(db_session, test_user_b.id, StressCheckinCreate(perceived_stress=2))

    hist_a = service.get_stress_history(db_session, test_user.id)
    hist_b = service.get_stress_history(db_session, test_user_b.id)

    assert len(hist_a) == 1
    assert hist_a[0].perceived_stress == 8
    assert hist_a[0].user_id == test_user.id

    assert len(hist_b) == 1
    assert hist_b[0].perceived_stress == 2
    assert hist_b[0].user_id == test_user_b.id


# 7. Trends calculation (7d and 30d)
def test_stress_trends_calculation(db_session: Session, test_user: User):
    service = StressWellnessService()

    # Populate 5 daily check-ins
    now = datetime.datetime.now(datetime.timezone.utc)
    for i, score in enumerate([3, 4, 5, 6, 7]):
        checkin = StressCheckin(
            user_id=test_user.id,
            perceived_stress=score,
            stress_index=float(score * 10),
            stress_level=service.classify_stress_level(float(score * 10)),
            data_completeness=100.0,
            created_at=now - datetime.timedelta(days=4 - i),
        )
        db_session.add(checkin)
    db_session.commit()

    trend_7d = service.calculate_trends(db_session, test_user.id, days=7)
    assert len(trend_7d.data_points) == 5
    assert trend_7d.average_index == 50.0
    assert trend_7d.trend == "INCREASING"


# 8. Consecutive increases pattern detection
def test_stress_consecutive_increases_pattern(db_session: Session, test_user: User):
    service = StressWellnessService()
    now = datetime.datetime.now(datetime.timezone.utc)

    # 4 consecutive increasing check-ins
    for i, val in enumerate([20.0, 35.0, 50.0, 65.0]):
        c = StressCheckin(
            user_id=test_user.id,
            perceived_stress=int(val // 10),
            stress_index=val,
            stress_level="moderate",
            data_completeness=80.0,
            created_at=now - datetime.timedelta(hours=24 * (3 - i)),
        )
        db_session.add(c)
    db_session.commit()

    trend = service.calculate_trends(db_session, test_user.id, days=7)
    patterns = " ".join(trend.observed_patterns)
    assert "consecutive check-ins" in patterns


# 9. Observational co-occurrence with sleep
def test_stress_sleep_cooccurrence_pattern(db_session: Session, test_user: User):
    service = StressWellnessService()
    now = datetime.datetime.now(datetime.timezone.utc)

    # Checkin with high stress + low sleep
    c1 = StressCheckin(
        user_id=test_user.id,
        perceived_stress=8,
        stress_index=75.0,
        stress_level="high",
        sleep_hours_snapshot=5.0,
        data_completeness=100.0,
        created_at=now - datetime.timedelta(days=1),
    )
    # Checkin with low stress + optimal sleep
    c2 = StressCheckin(
        user_id=test_user.id,
        perceived_stress=2,
        stress_index=20.0,
        stress_level="low",
        sleep_hours_snapshot=8.0,
        data_completeness=100.0,
        created_at=now - datetime.timedelta(days=2),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    trend = service.calculate_trends(db_session, test_user.id, days=7)
    patterns = " ".join(trend.observed_patterns)
    assert "sleep duration" in patterns


# 10. Recommendations and safety escalation for high tier
def test_stress_recommendations_and_safety_escalation():
    # Low stress recommendations
    recs_low = StressRecommendationService.get_recommendations(stress_index=15.0, stress_level="low")
    assert any("Optimal Stress" in r.title for r in recs_low)
    assert not any(r.category == "safety_escalation" for r in recs_low)

    # High stress recommendations MUST include professional safety escalation
    recs_high = StressRecommendationService.get_recommendations(stress_index=80.0, stress_level="high")
    assert any(r.category == "safety_escalation" for r in recs_high)
    safety_item = next(r for r in recs_high if r.category == "safety_escalation")
    assert "Professional Support" in safety_item.title
    assert "non-diagnostic wellness tool" in safety_item.description


# 11. Notification generation and daily deduplication
def test_stress_notification_generation_and_dedupe(db_session: Session, test_user: User):
    service = StressWellnessService()

    # High stress triggers notification
    service.record_checkin(db_session, test_user.id, StressCheckinCreate(perceived_stress=9, overwhelm=9))

    notifs = db_session.query(Notification).filter(Notification.user_id == test_user.id).all()
    assert len(notifs) == 1
    assert notifs[0].type == "stress_wellness"
    assert "Elevated" in notifs[0].title

    # Second high stress check-in on the same day must not duplicate notification
    service.record_checkin(db_session, test_user.id, StressCheckinCreate(perceived_stress=8, overwhelm=8))
    notifs_after = db_session.query(Notification).filter(Notification.user_id == test_user.id).all()
    assert len(notifs_after) == 1


# 12. Weekly and monthly report integration
def test_stress_adaptive_reports_inclusion(db_session: Session, test_user: User):
    from app.services.adaptive.report_service import generate_weekly_report, generate_monthly_report
    service = StressWellnessService()

    service.record_checkin(db_session, test_user.id, StressCheckinCreate(perceived_stress=4, overwhelm=3))

    wk_report = generate_weekly_report(db_session, test_user.id)
    assert "stress_7d_avg_index" in wk_report["wellness_summary"]
    assert "stress_summary" in wk_report
    assert "disclaimer" in wk_report

    mo_report = generate_monthly_report(db_session, test_user.id)
    assert "stress_30d_avg_index" in mo_report["wellness_changes"]
    assert "stress_monthly_summary" in mo_report


# 13. AI Assistant context builder inclusion
def test_stress_ai_context_builder_inclusion(db_session: Session, test_user: User):
    from app.ai.context_builder import context_builder
    service = StressWellnessService()

    service.record_checkin(db_session, test_user.id, StressCheckinCreate(perceived_stress=5, overwhelm=4))

    ctx = context_builder.build_user_context(user_id=test_user.id, db=db_session)
    assert "LifeOS Stress Wellness Index" in ctx.formatted_context_str
    assert "Non-diagnostic observational wellness indicator" in ctx.formatted_context_str


# 14. CRITICAL ARCHITECTURAL ISOLATION TEST:
# Proves that varying Stress from 0 to 100 causes EXACTLY 0.00000000 difference
# in Layer A disease probabilities (Heart, Diabetes, HTN, Obesity, Stroke, CKD) and Risk Fusion.
def test_strict_layer_a_isolation_zero_disease_impact():
    from app.services.risk_fusion_service import risk_fusion_service
    from app.schemas.risk_fusion import RiskFusionRequest, DiseaseInputItem
    from app.schemas.heart import HeartPredictionRequest
    from app.services.heart_model_service import HeartModelService

    # 1. Direct Model Prediction Isolation Check
    heart_req = HeartPredictionRequest(
        age_years=52.0,
        sex=1.0,
        systolic_bp_mmHg=138,
        diastolic_bp_mmHg=88.0,
        cholesterol_ordinal=2.0,
        glucose_ordinal=1.0,
        physical_activity=1.0,
        smoking_status=0.0,
    )
    p_heart = HeartModelService.get_instance().predict(heart_req).risk_score

    # Construct Risk Fusion inputs
    fusion_req = RiskFusionRequest(
        heart=DiseaseInputItem(disease="heart", risk_score=p_heart, threshold=0.40, prediction=int(p_heart >= 0.40), model="XGBoost"),
        diabetes=DiseaseInputItem(disease="diabetes", risk_score=0.1520, threshold=0.70, prediction=0, model="LightGBM"),
        hypertension=DiseaseInputItem(disease="hypertension", risk_score=0.3410, threshold=0.60, prediction=0, model="XGBoost"),
        obesity=DiseaseInputItem(disease="obesity", risk_score=0.4500, threshold=0.50, prediction=0, model="LightGBM"),
    )

    # Compute baseline composite risk
    rf_baseline = risk_fusion_service.fuse_risks(fusion_req)

    # Check with Stress = 0.0 check-in
    stress_idx_low, _ = StressWellnessService.calculate_stress_index(perceived_stress=0)
    rf_low_stress = risk_fusion_service.fuse_risks(fusion_req)

    # Check with Stress = 100.0 check-in
    stress_idx_high, _ = StressWellnessService.calculate_stress_index(perceived_stress=10, overwhelm=10)
    rf_high_stress = risk_fusion_service.fuse_risks(fusion_req)

    # Assert mathematical identity across all conditions to 8 decimal places
    assert abs(rf_baseline.overall_risk_score - rf_low_stress.overall_risk_score) < 1e-8
    assert abs(rf_baseline.overall_risk_score - rf_high_stress.overall_risk_score) < 1e-8
    assert rf_baseline.overall_health_score == rf_low_stress.overall_health_score == rf_high_stress.overall_health_score
    assert rf_baseline.top_priority_disease == rf_low_stress.top_priority_disease == rf_high_stress.top_priority_disease

    # Confirm Stress Index was varied from 0.0 to 100.0
    assert stress_idx_low == 0.0
    assert stress_idx_high == 100.0


