from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


TrendDirection = Literal["increasing", "decreasing", "stable"]


class MetricTrendItem(BaseModel):
    metric: str = Field(..., description="Metric identifier")
    display_name: str = Field(..., description="Human readable metric name")
    current_value: float = Field(..., description="Latest snapshot value")
    previous_value: float | None = Field(None, description="Previous snapshot value")
    absolute_change: float = Field(..., description="Signed absolute change (current - previous)")
    percentage_change: float | None = Field(None, description="Percentage change if baseline valid")
    direction: TrendDirection = Field(..., description="Trend direction")


class RiskTrendSummary(BaseModel):
    overall: MetricTrendItem
    heart: MetricTrendItem | None = None
    diabetes: MetricTrendItem | None = None
    hypertension: MetricTrendItem | None = None
    obesity: MetricTrendItem | None = None


class HealthSnapshot(BaseModel):
    id: str = Field(..., description="Unique snapshot identifier")
    timestamp: str = Field(..., description="ISO 8601 creation timestamp")
    assessment_input: dict[str, Any] = Field(default={}, description="Raw universal assessment inputs")
    disease_results: dict[str, Any] = Field(default={}, description="Heart, Diabetes, Hypertension, Obesity results")
    risk_fusion: dict[str, Any] | None = Field(None, description="Risk Fusion output summary")
    recommendations: list[dict[str, Any]] = Field(default=[], description="Generated recommendations list")


class HealthHistoryResponse(BaseModel):
    snapshots: list[HealthSnapshot] = Field(..., description="List of health snapshots (newest first)")
    total_count: int = Field(..., description="Total snapshot count")


class HealthTrendPoint(BaseModel):
    snapshot_id: str
    timestamp: str
    overall_risk_score: float
    overall_health_score: int
    heart_risk: float | None = None
    diabetes_risk: float | None = None
    hypertension_risk: float | None = None
    obesity_risk: float | None = None
    bmi: float | None = None
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    glucose: float | None = None
    hba1c: float | None = None


class HealthTrendSummary(BaseModel):
    trend_points: list[HealthTrendPoint] = Field(..., description="Chronological trend data points")
    risk_trends: RiskTrendSummary = Field(..., description="Summary of risk changes current vs previous")
    biomarker_trends: list[MetricTrendItem] = Field(default=[], description="Biomarker metric changes")
    total_snapshots_evaluated: int = Field(..., description="Count of snapshots evaluated for trend")
