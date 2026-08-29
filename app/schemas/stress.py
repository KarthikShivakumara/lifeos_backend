from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

NON_DIAGNOSTIC_DISCLAIMER = (
    "Wellness indicator — not a medical diagnosis. LifeOS provides observational lifestyle decision support. "
    "If experiencing persistent or severe distress, please consult a licensed healthcare professional."
)


class StressCheckinCreate(BaseModel):
    perceived_stress: int = Field(..., ge=0, le=10, description="How stressed have you felt today? (0=None, 10=Extreme)")
    overwhelm: int | None = Field(None, ge=0, le=10, description="How overwhelmed have you felt today? (0=None, 10=Extreme)")
    difficulty_relaxing: int | None = Field(None, ge=0, le=10, description="Difficulty unwinding or relaxing (0=None, 10=Extreme)")
    mood: int | None = Field(None, ge=0, le=10, description="Overall emotional state (0=Very Low, 10=Very Good)")
    energy: int | None = Field(None, ge=0, le=10, description="Physical & mental energy level (0=Exhausted, 10=Excellent)")
    notes: str | None = Field(None, max_length=500, description="Optional personal reflection or context note")


class StressCheckinResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    perceived_stress: int
    overwhelm: int | None = None
    difficulty_relaxing: int | None = None
    mood: int | None = None
    energy: int | None = None
    sleep_hours_snapshot: float | None = None
    activity_minutes_snapshot: int | None = None
    stress_index: float
    stress_level: str
    data_completeness: float
    is_diagnostic: bool = False
    recommendations: list[str] = []
    notes: str | None = None

    class Config:
        from_attributes = True


class StressCurrentResponse(BaseModel):
    current_index: float | None = None
    current_level: str | None = None
    data_completeness: float | None = None
    latest_checkin: StressCheckinResponse | None = None
    rolling_7d_avg: float | None = None
    rolling_30d_avg: float | None = None
    trend: str = "INSUFFICIENT_DATA"
    is_diagnostic: bool = False
    disclaimer: str = NON_DIAGNOSTIC_DISCLAIMER
    recommendations: list[str] = []


class StressTrendPoint(BaseModel):
    date: str
    stress_index: float
    stress_level: str
    sleep_hours: float | None = None
    activity_minutes: int | None = None


class StressTrendResponse(BaseModel):
    days_requested: int
    data_points: list[StressTrendPoint]
    average_index: float | None = None
    trend: str = "INSUFFICIENT_DATA"
    observed_patterns: list[str] = []
    is_diagnostic: bool = False
    disclaimer: str = NON_DIAGNOSTIC_DISCLAIMER


class StressSummaryResponse(BaseModel):
    total_checkins_30d: int
    average_index_30d: float | None = None
    highest_index_30d: float | None = None
    lowest_index_30d: float | None = None
    consistency_score: float = 0.0
    trend: str = "INSUFFICIENT_DATA"
    level_distribution: dict[str, int] = {}
    is_diagnostic: bool = False
    disclaimer: str = NON_DIAGNOSTIC_DISCLAIMER


class StressRecommendationItem(BaseModel):
    title: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW
    category: str  # recovery, sleep, activity, relaxation, social_support, safety_escalation
