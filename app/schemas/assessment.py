from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class HealthAssessmentCreate(BaseModel):
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=350)
    bmi: float | None = Field(default=None, ge=10, le=80)
    glucose: float | None = Field(default=None, ge=20, le=600)
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    cholesterol: float | None = Field(default=None, ge=50, le=500)
    heart_rate: int | None = None
    spo2: int | None = None
    smoking_status: str | None = None
    alcohol_use: str | None = None
    exercise_frequency: str | None = None
    diet_quality: str | None = None
    stress_level: str | None = None
    depression_score: float | None = Field(default=None, ge=0, le=100)
    family_history_diabetes: str | None = None
    family_history_heart_disease: str | None = None
    family_history_stroke: str | None = None
    water_intake_l: float | None = Field(default=None, ge=0, le=20)
    sleep_hours: float | None = None
    notes: str | None = None


class HealthAssessmentRead(ORMModel):
    id: str
    user_id: str
    bmi: float | None
    systolic_bp: int | None
    diastolic_bp: int | None
    heart_rate: int | None
    spo2: int | None
    smoking_status: str | None
    alcohol_use: str | None
    exercise_frequency: str | None
    diet_quality: str | None
    stress_level: str | None
    sleep_hours: float | None
    notes: str | None
    created_at: datetime


class HealthTwinRead(BaseModel):
    user_id: str
    health_score: float
    lifestyle_score: float
    wellness_score: float
    risk_band: str
    summary: str
    last_updated: str
