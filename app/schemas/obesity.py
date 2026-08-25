from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ObesityPredictionRequest(BaseModel):
    age_years: float = Field(..., ge=14.0, le=100.0, description="Age in years (14-100)")
    sex: float = Field(..., ge=0.0, le=1.0, description="Biological sex (0.0 = Female, 1.0 = Male)")
    family_history_obesity: float | None = Field(None, ge=0.0, le=1.0, description="Family history of obesity (0.0 = No, 1.0 = Yes)")
    frequent_high_calorie_food: float | None = Field(None, ge=0.0, le=1.0, description="Frequent high-calorie food intake (0.0 = No, 1.0 = Yes)")
    vegetable_consumption: float | None = Field(None, ge=1.0, le=3.0, description="Vegetable consumption frequency (1.0 - 3.0 scale)")
    meals_per_day: float | None = Field(None, ge=1.0, le=4.0, description="Main meals per day (1.0 - 4.0 scale)")
    between_meal_eating: float | None = Field(None, ge=0.0, le=3.0, description="Eating between meals (0=No, 1=Sometimes, 2=Freq, 3=Always)")
    smoking_status: float | None = Field(None, ge=0.0, le=1.0, description="Smoking status (0.0 = Non-smoker, 1.0 = Smoker)")
    water_intake_l: float | None = Field(None, ge=1.0, le=3.0, description="Daily water intake in liters (1.0 - 3.0)")
    calorie_monitoring: float | None = Field(None, ge=0.0, le=1.0, description="Calorie consumption monitoring (0.0 = No, 1.0 = Yes)")
    physical_activity_frequency: float | None = Field(None, ge=0.0, le=3.0, description="Physical activity frequency in days/week (0.0 - 3.0)")
    technology_usage_hours: float | None = Field(None, ge=0.0, le=2.0, description="Technology device usage hours/day (0.0 - 2.0)")
    alcohol_use: float | None = Field(None, ge=0.0, le=3.0, description="Alcohol consumption (0=No, 1=Sometimes, 2=Freq, 3=Always)")
    transportation_mode: float | None = Field(None, ge=0.0, le=1.0, description="Transportation mode (0.0 = Active, 1.0 = Sedentary)")


class ObesityPredictionResponse(BaseModel):
    disease: str = "obesity"
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability score [0.0 - 1.0]")
    risk_level: Literal["low", "moderate", "high"] = Field(..., description="Prototype risk band")
    threshold: float = Field(0.50, description="Operating threshold (0.50)")
    prediction: int = Field(..., description="Binary prediction (0 = Low/Normal Risk, 1 = Elevated Risk)")
    model: str = "LightGBM"
    model_version: str = "1.0.0"


class ObesityFeatureContribution(BaseModel):
    feature: str
    contribution: float
    direction: Literal["increases_risk", "decreases_risk"]
    human_readable: str


class ObesityExplanationResponse(BaseModel):
    disease: str = "obesity"
    risk_score: float
    risk_level: Literal["low", "moderate", "high"]
    threshold: float = 0.50
    prediction: int
    model: str = "LightGBM"
    model_version: str = "1.0.0"
    top_contributors: list[ObesityFeatureContribution]


class ObesityHealthCheckResponse(BaseModel):
    status: str
    obesity_model: str
    model: str
    version: str
