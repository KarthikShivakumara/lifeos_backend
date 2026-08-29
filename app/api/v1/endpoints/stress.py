from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stress import (
    NON_DIAGNOSTIC_DISCLAIMER,
    StressCheckinCreate,
    StressCheckinResponse,
    StressCurrentResponse,
    StressRecommendationItem,
    StressSummaryResponse,
    StressTrendResponse,
)
from app.services.stress_recommendation_service import StressRecommendationService
from app.services.stress_wellness_service import stress_wellness_service

router = APIRouter(prefix="/stress", tags=["Stress Wellness Intelligence"])


@router.post(
    "/checkins",
    response_model=StressCheckinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Daily Stress Wellness Check-in",
    description="Saves a user self-reported stress check-in, computes the LifeOS Stress Wellness Index, and records immutable history.",
)
def create_checkin(
    payload: StressCheckinCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StressCheckinResponse:
    try:
        return stress_wellness_service.record_checkin(db, current_user.id, payload)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record stress check-in: {str(err)}",
        )


@router.get(
    "/current",
    response_model=StressCurrentResponse,
    summary="Get Current Stress Wellness Status",
    description="Returns latest stress index, category, rolling 7-day & 30-day averages, trend, and active recommendations.",
)
def get_current(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StressCurrentResponse:
    return stress_wellness_service.get_current_stress(db, current_user.id)


@router.get(
    "/history",
    response_model=list[StressCheckinResponse],
    summary="Get Historical Stress Check-ins",
    description="Returns chronological list of immutable check-in records for the authenticated user.",
)
def get_history(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StressCheckinResponse]:
    return stress_wellness_service.get_stress_history(db, current_user.id, limit=limit)


@router.get(
    "/trends",
    response_model=StressTrendResponse,
    summary="Get Stress Wellness Trends & Patterns",
    description="Returns daily data points, rolling averages, trend classification (IMPROVING/STABLE/INCREASING), and observational lifestyle pattern insights.",
)
def get_trends(
    days: int = Query(default=7, ge=2, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StressTrendResponse:
    return stress_wellness_service.calculate_trends(db, current_user.id, days=days)


@router.get(
    "/summary",
    response_model=StressSummaryResponse,
    summary="Get 30-Day Stress Overview & Consistency",
    description="Returns 30-day analytics including average index, highest, lowest, check-in consistency percentage, and category distribution.",
)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StressSummaryResponse:
    return stress_wellness_service.get_stress_summary(db, current_user.id)


@router.get(
    "/recommendations",
    response_model=list[StressRecommendationItem],
    summary="Get Stress Wellness Recommendations",
    description="Returns prioritized lifestyle, sleep, relaxation, and safety guidance tailored to current stress status.",
)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StressRecommendationItem]:
    current_status = stress_wellness_service.get_current_stress(db, current_user.id)
    idx = current_status.current_index or 20.0
    lvl = current_status.current_level or "low"
    sleep_h = current_status.latest_checkin.sleep_hours_snapshot if current_status.latest_checkin else None
    act_m = current_status.latest_checkin.activity_minutes_snapshot if current_status.latest_checkin else None
    return StressRecommendationService.get_recommendations(idx, lvl, sleep_h, act_m)
