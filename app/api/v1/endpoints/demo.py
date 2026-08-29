from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Path

from app.services.demo_simulation_service import demo_simulation_service

router = APIRouter()


@router.get("/users", response_model=list[dict[str, Any]])
def get_synthetic_users() -> list[dict[str, Any]]:
    """List all 7 synthetic demonstration users."""
    return demo_simulation_service.list_users()


@router.get("/users/{user_id}", response_model=dict[str, Any])
def get_synthetic_user_detail(
    user_id: str = Path(..., description="Synthetic user ID (e.g. demo-priya-02)"),
) -> dict[str, Any]:
    """Get full details and 7-day timeline for a synthetic user."""
    user = demo_simulation_service.get_user_detail(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Synthetic demonstration user not found.")
    return user


@router.get("/users/{user_id}/simulation/{day}", response_model=dict[str, Any])
def get_synthetic_user_day_simulation(
    user_id: str = Path(..., description="Synthetic user ID"),
    day: int = Path(..., ge=1, le=7, description="Day number (1 to 7)"),
) -> dict[str, Any]:
    """Get calculated metrics and recommendations for a specific day in the 7-day timeline."""
    day_data = demo_simulation_service.get_user_day(user_id, day)
    if not day_data:
        raise HTTPException(status_code=404, detail=f"Day {day} simulation data not found for user {user_id}.")
    return day_data


@router.get("/users/{user_id}/weekly-report", response_model=dict[str, Any])
def get_synthetic_user_weekly_report(
    user_id: str = Path(..., description="Synthetic user ID"),
) -> dict[str, Any]:
    """Generate synthesized 7-day weekly report for a synthetic user."""
    report = demo_simulation_service.generate_weekly_report(user_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Weekly report for synthetic user {user_id} not found.")
    return report
