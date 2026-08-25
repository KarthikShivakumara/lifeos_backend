from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional, get_db
from app.models.user import User
from app.schemas.history import (
    HealthHistoryResponse,
    HealthSnapshot,
    HealthTrendSummary,
)
from app.services.history_service import history_service

router = APIRouter()


@router.post("/history", response_model=HealthSnapshot, summary="Create Health Assessment Snapshot")
def create_snapshot(
    payload: HealthSnapshot,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> HealthSnapshot:
    """Store a completed health assessment snapshot into history (persistently tied to user)."""
    user_id = current_user.id if current_user else None
    return history_service.create_snapshot(
        assessment_input=payload.assessment_input,
        disease_results=payload.disease_results,
        risk_fusion=payload.risk_fusion,
        recommendations=payload.recommendations,
        custom_id=payload.id if payload.id and payload.id != "string" else None,
        custom_timestamp=payload.timestamp if payload.timestamp and payload.timestamp != "string" else None,
        user_id=user_id,
        db=db,
    )


@router.get("/history", response_model=HealthHistoryResponse, summary="List Health Assessment History")
def get_history(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> HealthHistoryResponse:
    """Get stored health assessment snapshots (user-isolated when authenticated)."""
    user_id = current_user.id if current_user else None
    return history_service.get_history(user_id=user_id, db=db)


@router.get("/history/trends", response_model=HealthTrendSummary, summary="Calculate Health Risk Trends")
@router.post("/history/trends", response_model=HealthTrendSummary, summary="Calculate Health Risk Trends from Snapshots")
def calculate_trends(
    snapshots_payload: list[HealthSnapshot] | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> HealthTrendSummary:
    """Calculate longitudinal risk and biomarker trends across historical snapshots."""
    user_id = current_user.id if current_user else None
    return history_service.calculate_trends(snapshots_payload, user_id=user_id, db=db)


@router.get("/history/{snapshot_id}", response_model=HealthSnapshot, summary="Get Single Health Snapshot Details")
def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> HealthSnapshot:
    """Get details of a specific health snapshot by ID (user ownership verified)."""
    user_id = current_user.id if current_user else None
    snap = history_service.get_snapshot(snapshot_id, user_id=user_id, db=db)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Health snapshot '{snapshot_id}' not found.")
    return snap


@router.delete("/history/{snapshot_id}", summary="Delete Single Health Snapshot")
def delete_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, str]:
    """Delete a specific health snapshot by ID (user ownership verified)."""
    user_id = current_user.id if current_user else None
    success = history_service.delete_snapshot(snapshot_id, user_id=user_id, db=db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Health snapshot '{snapshot_id}' not found.")
    return {"status": "ok", "deleted_id": snapshot_id}


@router.delete("/history", summary="Clear All Health History")
def clear_history(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """Clear all health assessment snapshots from history for the current user."""
    user_id = current_user.id if current_user else None
    count = history_service.clear_history(user_id=user_id, db=db)
    return {"status": "ok", "cleared_count": count}
