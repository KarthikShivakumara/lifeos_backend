from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ActivityPredictionRequest(BaseModel):
    gender: str = Field(..., description="Gender: 'male' or 'female'")
    age: float = Field(..., ge=10.0, le=100.0, description="Age in years")
    height: float = Field(..., ge=100.0, le=250.0, description="Height in cm")
    weight: float = Field(..., ge=30.0, le=250.0, description="Weight in kg")
    duration: float = Field(..., ge=1.0, le=300.0, description="Workout duration in minutes")
    heart_rate: float = Field(..., ge=40.0, le=220.0, description="Average heart rate during exercise (bpm)")
    body_temp: float = Field(..., ge=35.0, le=43.0, description="Body temperature after workout (°C)")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in ("male", "female"):
            raise ValueError("Gender must be 'male' or 'female'")
        return norm


class ActivityCaloriePredictionResponse(BaseModel):
    subsystem: Literal["activity_wellness"] = "activity_wellness"
    estimated_calories: float = Field(..., description="Estimated workout energy expenditure in kcal")
    duration_minutes: float = Field(..., description="Workout duration in minutes")
    model: str = "LightGBM Regressor"
    model_version: str = "1.0.0"


class ActivityEngineInput(BaseModel):
    daily_steps: int = Field(..., ge=0, le=100000, description="Total daily steps count")
    very_active_minutes: int = Field(0, ge=0, le=1440, description="Minutes of vigorous activity")
    fairly_active_minutes: int = Field(0, ge=0, le=1440, description="Minutes of moderate activity")
    lightly_active_minutes: int = Field(0, ge=0, le=1440, description="Minutes of light activity")
    sedentary_minutes: int = Field(0, ge=0, le=1440, description="Minutes of sedentary behavior")
    historical_steps: list[int] = Field(default_factory=list, description="Historical step counts for trend calculation")


class ActivitySignal(BaseModel):
    domain: Literal["activity"] = "activity"
    activity_score: float = Field(..., ge=0.0, le=100.0, description="Normalized Activity Score (0-100)")
    activity_level: Literal["low", "moderate", "optimal"] = Field(..., description="Qualitative activity level")
    sedentary_risk: Literal["low", "moderate", "elevated"] = Field(..., description="Sedentary risk classification")
    weekly_trend: Literal["IMPROVING", "STABLE", "DECLINING"] = Field(..., description="Longitudinal trend direction")
    exercise_consistency_pct: float = Field(..., ge=0.0, le=100.0, description="Consistency percentage")
    daily_steps: int = Field(..., description="Daily step count")
    active_minutes: int = Field(..., description="Total moderate-to-vigorous active minutes")
    sedentary_hours: float = Field(..., description="Sedentary duration in hours")
    estimated_workout_calories: float | None = Field(None, description="Optional workout calorie estimate if applicable")
    source: str = "hybrid_activity_engine"
    recommendation_triggers: list[str] = Field(default_factory=list, description="Triggers for decision support")
