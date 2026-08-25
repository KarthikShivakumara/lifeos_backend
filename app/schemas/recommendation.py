from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


RecommendationCategory = Literal[
    "nutrition",
    "physical_activity",
    "blood_pressure",
    "blood_glucose",
    "weight_management",
    "smoking",
    "alcohol",
    "sleep",
    "hydration",
    "stress_management",
    "medical_follow_up",
]

RecommendationPriority = Literal["low", "moderate", "high", "urgent"]


class RecommendationItem(BaseModel):
    id: str = Field(..., description="Unique recommendation ID")
    category: RecommendationCategory = Field(..., description="Target lifestyle / clinical category")
    priority: RecommendationPriority = Field(..., description="Urgency priority level")
    title: str = Field(..., description="Concise action title")
    description: str = Field(..., description="Detailed recommendation text")
    reason: str = Field(..., description="Explainable rationale (includes SHAP attribution or input finding)")
    related_diseases: list[str] = Field(default=[], description="List of associated disease verticals")
    source_feature: str | None = Field(None, description="Primary trigger feature identifier")
    action: str = Field(..., description="Actionable next step for the user")
    disclaimer: str = Field(
        "LifeOS recommendations provide lifestyle and wellness guidance. They are not medical prescriptions or diagnoses.",
        description="Category disclaimer"
    )


class RecommendationRequest(BaseModel):
    assessment_input: dict[str, Any] = Field(default={}, description="Raw universal assessment inputs")
    heart: dict[str, Any] | None = Field(None, description="Heart prediction result")
    diabetes: dict[str, Any] | None = Field(None, description="Diabetes prediction result")
    hypertension: dict[str, Any] | None = Field(None, description="Hypertension prediction result")
    obesity: dict[str, Any] | None = Field(None, description="Obesity prediction result")
    activity: dict[str, Any] | None = Field(None, description="Activity wellness signal or prediction result")
    risk_fusion: dict[str, Any] | None = Field(None, description="Risk Fusion result")


class RecommendationEngineResponse(BaseModel):
    recommendations: list[RecommendationItem] = Field(..., description="Complete sorted list of personalized recommendations")
    top_recommendations: list[RecommendationItem] = Field(..., description="Top 5 priority recommendations for dashboard display")
    total_count: int = Field(..., description="Total count of generated recommendations")
    generated_from: dict[str, bool] = Field(..., description="Status of input modules evaluated")
    disclaimer: str = Field(
        "LifeOS recommendations provide personalized health and lifestyle guidance based on machine-learning estimates and submitted health indicators. They do not constitute medical advice or a doctor's diagnosis.",
        description="System disclaimer"
    )
