from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StrokePredictionRequest(BaseModel):
    gender: str = Field(..., description="Gender: 'Male' or 'Female'")
    age: float = Field(..., ge=0.0, le=120.0, description="Age in years (0.0 - 120.0)")
    hypertension: int = Field(..., ge=0, le=1, description="Hypertension history: 0 = No, 1 = Yes")
    heart_disease: int = Field(..., ge=0, le=1, description="Heart disease history: 0 = No, 1 = Yes")
    ever_married: str = Field(..., description="Marital history: 'Yes' or 'No'")
    work_type: str = Field(..., description="Work classification: 'Private', 'Self-employed', 'Govt_job', 'children', 'Never_worked'")
    Residence_type: str = Field(..., description="Residence type: 'Urban' or 'Rural'")
    avg_glucose_level: float = Field(..., ge=40.0, le=350.0, description="Average blood glucose level in mg/dL")
    bmi: float | None = Field(None, ge=10.0, le=80.0, description="Body Mass Index in kg/m²")
    smoking_status: str = Field(..., description="Smoking status: 'formerly smoked', 'never smoked', 'smokes', 'Unknown'")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("Male", "Female"):
            raise ValueError("gender must be 'Male' or 'Female'")
        return v

    @field_validator("ever_married")
    @classmethod
    def validate_ever_married(cls, v: str) -> str:
        if v not in ("Yes", "No"):
            raise ValueError("ever_married must be 'Yes' or 'No'")
        return v

    @field_validator("work_type")
    @classmethod
    def validate_work_type(cls, v: str) -> str:
        valid_types = ("Private", "Self-employed", "Govt_job", "children", "Never_worked")
        if v not in valid_types:
            raise ValueError(f"work_type must be one of {valid_types}")
        return v

    @field_validator("Residence_type")
    @classmethod
    def validate_residence_type(cls, v: str) -> str:
        if v not in ("Urban", "Rural"):
            raise ValueError("Residence_type must be 'Urban' or 'Rural'")
        return v

    @field_validator("smoking_status")
    @classmethod
    def validate_smoking_status(cls, v: str) -> str:
        valid_statuses = ("formerly smoked", "never smoked", "smokes", "Unknown")
        if v not in valid_statuses:
            raise ValueError(f"smoking_status must be one of {valid_statuses}")
        return v


class StrokePredictionResponse(BaseModel):
    disease: Literal["stroke"] = "stroke"
    risk_score: float = Field(..., description="Estimated Calibrated Risk Score (0.0 to 1.0)")
    risk_level: Literal["low", "moderate", "high", "very_high"] = Field(..., description="Risk level category")
    threshold: float = Field(0.50, description="Operating threshold selected from validation set")
    prediction: int = Field(..., description="Binary risk prediction (0 = Low/Moderate Risk, 1 = High Risk)")
    model: str = "LightGBM"
    model_version: str = "1.0.0"


class FeatureContribution(BaseModel):
    feature: str = Field(..., description="Feature column name")
    contribution: float = Field(..., description="SHAP feature attribution value")
    direction: Literal["increases_risk", "decreases_risk"] = Field(..., description="Impact direction on risk prediction")
    human_readable: str = Field(..., description="Human-readable explanation of feature impact")


class StrokeExplanationResponse(BaseModel):
    disease: Literal["stroke"] = "stroke"
    base_value: float = Field(..., description="SHAP baseline expectation score")
    top_contributions: list[FeatureContribution] = Field(..., description="Ranked feature attributions")
    explanation_summary: str = Field(..., description="Summary explanation string")
