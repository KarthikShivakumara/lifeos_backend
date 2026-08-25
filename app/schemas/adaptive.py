from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class HealthEventCreate(BaseModel):
    event_type: str = Field(..., description="Event type (e.g. ASSESSMENT_COMPLETED, BP_RECORDED, SLEEP_RECORDED)")
    source: str = Field("user_input", description="Source of event")
    payload: dict[str, Any] | None = Field(default=None, description="Event payload dictionary")
    model_version: str | None = Field(default=None, description="Associated model version if applicable")
    consent_status: str = Field("granted", description="Consent status")


class HealthEventResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    timestamp: datetime
    source: str
    payload: dict[str, Any] | None
    model_version: str | None
    consent_status: str
    created_at: datetime


class PredictionSnapshotCreate(BaseModel):
    assessment_id: str | None = None
    model_name: str
    model_version: str
    probability: float
    threshold: float
    risk_category: str
    feature_snapshot: dict[str, Any] | None = None


class PredictionSnapshotResponse(BaseModel):
    id: str
    user_id: str
    assessment_id: str | None
    model_name: str
    model_version: str
    probability: float
    threshold: float
    risk_category: str
    feature_snapshot: dict[str, Any] | None
    timestamp: datetime


class UserBaselineResponse(BaseModel):
    metric: str
    baseline_value: float
    rolling_7_day_avg: float | None
    rolling_30_day_avg: float | None
    min_value: float | None
    max_value: float | None
    std_deviation: float | None
    current_deviation: float | None
    trend: Literal["IMPROVING", "STABLE", "DECLINING", "INSUFFICIENT_DATA"]
    consistency_score: float
    last_updated: datetime


class UserBaselineSummary(BaseModel):
    user_id: str
    baselines: list[UserBaselineResponse]
    evaluated_at: datetime


class RecommendationFeedbackCreate(BaseModel):
    recommendation_id: str
    action: Literal["ACCEPTED", "DISMISSED", "COMPLETED", "NOT_RELEVANT", "SNOOZED"]


class RecommendationFeedbackResponse(BaseModel):
    id: str
    user_id: str
    recommendation_id: str
    action: str
    timestamp: datetime


class OutcomeRecordCreate(BaseModel):
    related_prediction_id: str | None = None
    outcome_type: str = Field(..., description="LAB_RESULT, CLINICAL_FOLLOWUP, WEIGHT_CHANGE, etc.")
    outcome_value: float | None = None
    outcome_label: str | None = None
    measurement_date: datetime | None = None
    source: Literal["USER_REPORTED", "VERIFIED"] = "USER_REPORTED"
    verification_status: Literal["VERIFIED", "UNVERIFIED"] = "UNVERIFIED"
    consent_status: str = "granted"


class OutcomeRecordResponse(BaseModel):
    id: str
    user_id: str
    related_prediction_id: str | None
    outcome_type: str
    outcome_value: float | None
    outcome_label: str | None
    measurement_date: datetime
    source: str
    verification_status: str
    consent_status: str
    created_at: datetime


class WeeklyHealthReportResponse(BaseModel):
    report_id: str
    user_id: str
    period_start: str
    period_end: str
    clinical_screening_summary: dict[str, Any]
    wellness_summary: dict[str, Any]
    sleep_trend: str
    activity_trend: str
    nutrition_summary: dict[str, Any]
    improvements: list[str]
    declines: list[str]
    personalized_recommendations: list[str]
    disclaimer: str
    generated_at: datetime


class MonthlyHealthReportResponse(BaseModel):
    report_id: str
    user_id: str
    month_name: str
    clinical_changes: dict[str, Any]
    wellness_changes: dict[str, Any]
    consistency_score: float
    recommendation_adherence_rate: float
    key_focus_areas: list[str]
    summary_text: str
    disclaimer: str
    generated_at: datetime


class DriftReportResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    feature: str
    baseline_mean: float | None
    current_mean: float | None
    drift_score: float
    severity: str
    timestamp: datetime
