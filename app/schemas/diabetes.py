from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class DiabetesPredictionRequest(BaseModel):
    age_years: float = Field(..., ge=18.0, le=100.0, description="Age in years (18-100)")
    sex: float = Field(..., ge=0.0, le=1.0, description="Biological sex (0.0 = Female, 1.0 = Male)")
    bmi: float | None = Field(None, ge=10.0, le=80.0, description="Body Mass Index in kg/m²")
    blood_glucose_level: float | None = Field(None, ge=50.0, le=350.0, description="Fasting blood glucose level in mg/dL")
    hba1c_level: float | None = Field(None, ge=3.5, le=15.0, description="HbA1c percentage (%)")
    hypertension: float | None = Field(None, ge=0.0, le=1.0, description="History of hypertension (0.0 = No, 1.0 = Yes)")
    heart_disease: float | None = Field(None, ge=0.0, le=1.0, description="History of heart disease (0.0 = No, 1.0 = Yes)")
    smoking_status: float | None = Field(None, ge=0.0, le=1.0, description="Smoking status (0.0 = Non-smoker, 1.0 = Smoker)")


class DiabetesPredictionResponse(BaseModel):
    disease: str = "diabetes"
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability score [0.0 - 1.0]")
    risk_level: Literal["low", "moderate", "high"] = Field(..., description="Prototype risk band")
    threshold: float = Field(0.70, description="Operating threshold (0.70)")
    prediction: int = Field(..., description="Binary prediction (0 = Low/Normal Risk, 1 = Elevated Risk)")
    model: str = "LightGBM"
    model_version: str = "1.0.0"


class DiabetesFeatureContribution(BaseModel):
    feature: str
    contribution: float
    direction: Literal["increases_risk", "decreases_risk"]
    human_readable: str


class DiabetesExplanationResponse(BaseModel):
    disease: str = "diabetes"
    risk_score: float
    risk_level: Literal["low", "moderate", "high"]
    threshold: float = 0.70
    prediction: int
    model: str = "LightGBM"
    model_version: str = "1.0.0"
    top_contributors: list[DiabetesFeatureContribution]


class DiabetesHealthCheckResponse(BaseModel):
    status: str
    diabetes_model: str
    model: str
    version: str
