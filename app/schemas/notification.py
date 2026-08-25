from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

NotificationType = Literal["assessment_reminder", "high_risk_alert", "recommendation_reminder", "trend_alert", "system"]
NotificationPriority = Literal["low", "moderate", "high", "urgent"]


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    created_at: str
    action_url: str | None = "/dashboard"
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total_count: int
    unread_count: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationGenerateResponse(BaseModel):
    status: str
    generated_count: int
    notifications: list[NotificationResponse]
