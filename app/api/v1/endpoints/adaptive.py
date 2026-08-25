from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.adaptive import (
    HealthEventCreate,
    HealthEventResponse,
    MonthlyHealthReportResponse,
    OutcomeRecordCreate,
    OutcomeRecordResponse,
    RecommendationFeedbackCreate,
    RecommendationFeedbackResponse,
    UserBaselineResponse,
    UserBaselineSummary,
    WeeklyHealthReportResponse,
)
from app.services.adaptive.baseline_service import calculate_and_update_baselines, get_user_baselines
from app.services.adaptive.event_service import get_user_events, record_health_event
from app.services.adaptive.feedback_service import get_user_feedback, record_recommendation_feedback
from app.services.adaptive.outcome_service import get_user_outcomes, record_outcome
from app.services.adaptive.report_service import generate_monthly_report, generate_weekly_report
from app.services.adaptive.trend_service import evaluate_longitudinal_trends

router = APIRouter(prefix="/adaptive", tags=["Adaptive Intelligence & Longitudinal Reports"])


@router.get("/baseline", response_model=UserBaselineSummary, summary="Get Rolling Personal Baselines")
def get_baselines(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> UserBaselineSummary:
    """Returns 7-day and 30-day rolling baselines across 14 health metrics."""
    baselines = get_user_baselines(db, current_user.id)
    return UserBaselineSummary(
        user_id=current_user.id,
        baselines=[
            UserBaselineResponse(
                metric=b.metric,
                baseline_value=b.baseline_value,
                rolling_7_day_avg=b.rolling_7_day_avg,
                rolling_30_day_avg=b.rolling_30_day_avg,
                min_value=b.min_value,
                max_value=b.max_value,
                std_deviation=b.std_deviation,
                current_deviation=b.current_deviation,
                trend=b.trend,
                consistency_score=b.consistency_score,
                last_updated=b.last_updated,
            )
            for b in baselines
        ],
        evaluated_at=current_user.updated_at or current_user.created_at,
    )


@router.get("/trends", summary="Get Longitudinal Health Trends")
def get_trends(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Returns directional clinical and wellness trend synthesis."""
    return evaluate_longitudinal_trends(db, current_user.id)


@router.get("/reports/weekly", response_model=WeeklyHealthReportResponse, summary="Get Weekly Health Summary")
def get_weekly_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> WeeklyHealthReportResponse:
    """Generates non-diagnostic Weekly Health Summary."""
    report = generate_weekly_report(db, current_user.id)
    return WeeklyHealthReportResponse(**report)


@router.get("/reports/monthly", response_model=MonthlyHealthReportResponse, summary="Get Monthly Health Review")
def get_monthly_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MonthlyHealthReportResponse:
    """Generates 30-day longitudinal Monthly Health Review."""
    report = generate_monthly_report(db, current_user.id)
    return MonthlyHealthReportResponse(**report)


@router.post("/events", response_model=HealthEventResponse, summary="Log Health Event")
def log_event(
    payload: HealthEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HealthEventResponse:
    """Logs a user health event into the longitudinal event stream."""
    event = record_health_event(
        db=db,
        user_id=current_user.id,
        event_type=payload.event_type,
        payload=payload.payload,
        source=payload.source,
        model_version=payload.model_version,
        consent_status=payload.consent_status,
    )
    return HealthEventResponse(
        id=event.id,
        user_id=event.user_id,
        event_type=event.event_type,
        timestamp=event.timestamp,
        source=event.source,
        payload=event.payload,
        model_version=event.model_version,
        consent_status=event.consent_status,
        created_at=event.created_at,
    )


@router.post("/feedback", response_model=RecommendationFeedbackResponse, summary="Log Recommendation Feedback")
def log_feedback(
    payload: RecommendationFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationFeedbackResponse:
    """Logs user action on a recommendation (ACCEPTED, DISMISSED, COMPLETED, SNOOZED)."""
    fb = record_recommendation_feedback(
        db=db,
        user_id=current_user.id,
        recommendation_id=payload.recommendation_id,
        action=payload.action,
    )
    return RecommendationFeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        recommendation_id=fb.recommendation_id,
        action=fb.action,
        timestamp=fb.timestamp,
    )


@router.post("/outcomes", response_model=OutcomeRecordResponse, summary="Log Follow-up Outcome")
def log_outcome(
    payload: OutcomeRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutcomeRecordResponse:
    """Logs clinical follow-up or lab result outcome."""
    out = record_outcome(
        db=db,
        user_id=current_user.id,
        outcome_type=payload.outcome_type,
        outcome_value=payload.outcome_value,
        outcome_label=payload.outcome_label,
        measurement_date=payload.measurement_date,
        source=payload.source,
        verification_status=payload.verification_status,
        related_prediction_id=payload.related_prediction_id,
        consent_status=payload.consent_status,
    )
    return OutcomeRecordResponse(
        id=out.id,
        user_id=out.user_id,
        related_prediction_id=out.related_prediction_id,
        outcome_type=out.outcome_type,
        outcome_value=out.outcome_value,
        outcome_label=out.outcome_label,
        measurement_date=out.measurement_date,
        source=out.source,
        verification_status=out.verification_status,
        consent_status=out.consent_status,
        created_at=out.created_at,
    )
