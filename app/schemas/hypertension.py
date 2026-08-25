from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class HypertensionPredictionRequest(BaseModel):
    age_years: float = Field(..., ge=18.0, le=100.0, description="Age in years (18-100)")
    sex: float = Field(..., ge=0.0, le=1.0, description="Biological sex (0.0 = Female, 1.0 = Male)")
    systolic_bp_mmHg: float = Field(..., ge=70.0, le=250.0, description="Systolic Blood Pressure in mmHg")
    diastolic_bp_mmHg: float = Field(..., ge=40.0, le=150.0, description="Diastolic Blood Pressure in mmHg")
    bmi: float | None = Field(None, ge=10.0, le=80.0, description="Body Mass Index in kg/m²")
    heart_rate: float | None = Field(None, ge=40.0, le=220.0, description="Resting heart rate in bpm")
    cholesterol: float | None = Field(None, ge=50.0, le=600.0, description="Total cholesterol in mg/dL")
    glucose: float | None = Field(None, ge=40.0, le=400.0, description="Fasting blood glucose level in mg/dL")
    smoking_status: float | None = Field(None, ge=0.0, le=1.0, description="Smoking status (0.0 = Non-smoker, 1.0 = Smoker)")
    physical_activity: float | None = Field(None, ge=0.0, le=1.0, description="Physical activity (0.0 = Inactive, 1.0 = Active)")
    stress_level: float | None = Field(None, ge=0.0, le=1.0, description="Stress level (0.0 = Low, 1.0 = Moderate/High)")


class HypertensionPredictionResponse(BaseModel):
    disease: str = "hypertension"
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability score [0.0 - 1.0]")
    risk_level: Literal["low", "moderate", "high"] = Field(..., description="Prototype risk band")
    threshold: float = Field(0.60, description="Operating threshold (0.60)")
    prediction: int = Field(..., description="Binary prediction (0 = Low/Normal Risk, 1 = Elevated Risk)")
    model: str = "XGBoost"
    model_version: str = "1.0.0"


class HypertensionFeatureContribution(BaseModel):
    feature: str
    contribution: float
    direction: Literal["increases_risk", "decreases_risk"]
    human_readable: str


class HypertensionExplanationResponse(BaseModel):
    disease: str = "hypertension"
    risk_score: float
    risk_level: Literal["low", "moderate", "high"]
    threshold: float = 0.60
    prediction: int
    model: str = "XGBoost"
    model_version: str = "1.0.0"
    top_contributors: list[HypertensionFeatureContribution]


class HypertensionHealthCheckResponse(BaseModel):
    status: str
    hypertension_model: str
    model: str
    version: str
