from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HeartPredictionRequest(BaseModel):
    age_years: float = Field(..., ge=18.0, le=100.0, description="Age in years (18.0 - 100.0)")
    sex: float = Field(..., description="Sex: 0.0 for Female, 1.0 for Male")
    height_cm: float | None = Field(None, ge=100.0, le=220.0, description="Height in cm (100.0 - 220.0)")
    weight_kg: float | None = Field(None, ge=30.0, le=250.0, description="Weight in kg (30.0 - 250.0)")
    bmi: float | None = Field(None, ge=10.0, le=80.0, description="BMI in kg/m² (10.0 - 80.0)")
    systolic_bp_mmHg: int = Field(..., ge=70, le=250, description="Systolic blood pressure in mmHg (70 - 250)")
    diastolic_bp_mmHg: float | None = Field(None, ge=40.0, le=150.0, description="Diastolic blood pressure in mmHg (40.0 - 150.0)")
    smoking_status: float | None = Field(None, description="Smoking status: 0.0 = Non-smoker, 1.0 = Smoker")
    alcohol_status: float | None = Field(None, description="Alcohol intake: 0.0 = Non-drinker, 1.0 = Drinker")
    physical_activity: float | None = Field(None, description="Physical activity: 0.0 = Inactive, 1.0 = Active")
    cholesterol_ordinal: float | None = Field(None, description="Cholesterol level: 1.0 = Normal, 2.0 = Above Normal, 3.0 = High")
    glucose_ordinal: float | None = Field(None, description="Glucose level: 1.0 = Normal, 2.0 = Above Normal, 3.0 = High")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: float) -> float:
        if v not in (0.0, 1.0):
            raise ValueError("sex must be 0.0 (Female) or 1.0 (Male)")
        return v

    @field_validator("smoking_status", "alcohol_status", "physical_activity")
    @classmethod
    def validate_binary_status(cls, v: float | None) -> float | None:
        if v is not None and v not in (0.0, 1.0):
            raise ValueError("Binary status attributes must be 0.0 or 1.0")
        return v

    @field_validator("cholesterol_ordinal", "glucose_ordinal")
    @classmethod
    def validate_ordinal_levels(cls, v: float | None) -> float | None:
        if v is not None and v not in (1.0, 2.0, 3.0):
            raise ValueError("Ordinal levels must be 1.0 (Normal), 2.0 (Above Normal), or 3.0 (High)")
        return v


class HeartPredictionResponse(BaseModel):
    disease: Literal["heart_disease"] = "heart_disease"
    risk_score: float = Field(..., description="Estimated Risk Score (0.0 to 1.0)")
    risk_level: Literal["low", "moderate", "high"] = Field(..., description="Prototype risk category: low (<0.25), moderate (0.25-0.40), high (>=0.40)")
    threshold: float = Field(0.40, description="Operating threshold selected from validation set")
    prediction: int = Field(..., description="Binary risk prediction (0 = Low/Moderate Risk, 1 = High Risk)")
    model: str = "XGBoost"
    model_version: str = "1.0.0"


class FeatureContribution(BaseModel):
    feature: str = Field(..., description="Feature column name")
    contribution: float = Field(..., description="SHAP feature attribution value")
    direction: Literal["increases_risk", "decreases_risk"] = Field(..., description="Impact direction on risk prediction")
    human_readable: str = Field(..., description="Human-readable explanation of feature impact")


class HeartExplanationResponse(BaseModel):
    disease: Literal["heart_disease"] = "heart_disease"
    risk_score: float
    risk_level: Literal["low", "moderate", "high"]
    threshold: float = 0.40
    prediction: int
    model: str = "XGBoost"
    model_version: str = "1.0.0"
    top_contributors: list[FeatureContribution] = Field(..., description="Top 5 feature contributors to estimated risk score")


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    heart_model: str = "loaded"
    model: str = "XGBoost"
    version: str = "1.0.0"
