from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationGenerateResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_generator import notification_generator
from app.services.notification_service import notification_service

router = APIRouter()


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="List Notifications",
)
def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """Retrieve notifications belonging to the authenticated user."""
    return notification_service.list_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        db=db,
    )


@router.get(
    "/notifications/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get Unread Notification Count",
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationUnreadCountResponse:
    """Retrieve total count of unread notifications for the authenticated user."""
    return notification_service.get_unread_count(user_id=current_user.id, db=db)


@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
)
def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Mark a specific notification as read (user isolation enforced)."""
    return notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
        db=db,
    )


@router.put(
    "/notifications/read-all",
    response_model=NotificationUnreadCountResponse,
    summary="Mark All Notifications as Read",
)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationUnreadCountResponse:
    """Mark all notifications of the authenticated user as read."""
    return notification_service.mark_all_as_read(user_id=current_user.id, db=db)


@router.delete(
    "/notifications/{notification_id}",
    summary="Delete Notification",
)
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Dismiss/delete a specific notification (user isolation enforced)."""
    return notification_service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id,
        db=db,
    )


@router.post(
    "/notifications/generate",
    response_model=NotificationGenerateResponse,
    summary="Generate Health Notifications",
)
def generate_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationGenerateResponse:
    """Trigger rule-based notification generation from user's latest health state."""
    created = notification_generator.generate_for_user(user_id=current_user.id, db=db)
    return NotificationGenerateResponse(
        status="ok",
        generated_count=len(created),
        notifications=created,
    )
