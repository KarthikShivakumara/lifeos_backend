from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SleepPredictionRequest(BaseModel):
    gender: str = Field(..., description="Gender: 'Male' or 'Female'")
    age: float = Field(..., ge=18.0, le=100.0, description="Age in years")
    occupation: str = Field(..., description="Occupation title (e.g. 'Doctor', 'Engineer', 'Nurse', 'Other')")
    sleep_duration: float = Field(..., ge=3.0, le=12.0, description="Daily sleep duration in hours")
    quality_of_sleep: float = Field(..., ge=1.0, le=10.0, description="Self-reported sleep quality scale (1 - 10)")
    physical_activity_level: float = Field(..., ge=0.0, le=300.0, description="Daily physical activity in minutes")
    stress_level: float = Field(..., ge=1.0, le=10.0, description="Self-reported stress level scale (1 - 10)")
    bmi_category: str = Field(..., description="BMI category: 'Normal', 'Overweight', or 'Obese'")
    systolic_bp: float = Field(..., ge=70.0, le=220.0, description="Systolic blood pressure in mmHg")
    diastolic_bp: float = Field(..., ge=40.0, le=140.0, description="Diastolic blood pressure in mmHg")
    heart_rate: float = Field(..., ge=40.0, le=160.0, description="Resting heart rate in bpm")
    daily_steps: float = Field(..., ge=500.0, le=30000.0, description="Daily step count")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("Male", "Female"):
            raise ValueError("Gender must be 'Male' or 'Female'")
        return v

    @field_validator("bmi_category")
    @classmethod
    def validate_bmi(cls, v: str) -> str:
        norm = v.strip()
        if norm == "Normal Weight":
            return "Normal"
        if norm not in ("Normal", "Overweight", "Obese"):
            raise ValueError("bmi_category must be 'Normal', 'Overweight', or 'Obese'")
        return norm


class SleepPredictionResponse(BaseModel):
    subsystem: Literal["sleep_wellness"] = "sleep_wellness"
    risk_score: float = Field(..., description="Estimated Calibrated Sleep Risk Probability (0.0 to 1.0)")
    risk_level: Literal["low", "moderate", "elevated"] = Field(..., description="Sleep risk level category")
    threshold: float = Field(0.65, description="Operating threshold selected from validation set")
    prediction: int = Field(..., description="Binary risk prediction (0 = Low Risk, 1 = Elevated Sleep Risk)")
    model: str = "Logistic Regression"
    model_version: str = "1.0.0"


class FeatureContribution(BaseModel):
    feature: str = Field(..., description="Feature column name")
    contribution: float = Field(..., description="SHAP feature attribution value")
    direction: Literal["increases_risk", "decreases_risk"] = Field(..., description="Impact direction on sleep risk")
    human_readable: str = Field(..., description="Human-readable explanation of feature impact")


class SleepExplanationResponse(BaseModel):
    subsystem: Literal["sleep_wellness"] = "sleep_wellness"
    base_value: float = Field(..., description="SHAP baseline expectation score")
    top_contributions: list[FeatureContribution] = Field(..., description="Ranked feature attributions")
    explanation_summary: str = Field(..., description="Summary explanation string")
