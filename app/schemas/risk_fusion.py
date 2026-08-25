from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class DiseaseInputItem(BaseModel):
    disease: str = Field(..., description="Disease identifier ('heart', 'diabetes', 'hypertension', 'obesity')")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated raw probability score [0.0 - 1.0]")
    prediction: int = Field(..., description="Binary prediction decision (0 or 1)")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Model operating decision threshold")
    model: str = Field(..., description="Model name (e.g. 'XGBoost', 'LightGBM')")
    model_version: str = Field("1.0.0", description="Model artifact version")
    top_contributors: list[dict[str, Any]] | None = Field(default=[], description="Top SHAP feature attributions")


class RiskFusionRequest(BaseModel):
    heart: DiseaseInputItem | None = Field(None, description="Heart Disease prediction result")
    diabetes: DiseaseInputItem | None = Field(None, description="Diabetes prediction result")
    hypertension: DiseaseInputItem | None = Field(None, description="Hypertension prediction result")
    obesity: DiseaseInputItem | None = Field(None, description="Obesity prediction result")


class RankedDiseaseItem(BaseModel):
    rank: int = Field(..., description="Priority rank (1 = Highest Risk)")
    disease: str = Field(..., description="Disease identifier")
    display_name: str = Field(..., description="Human readable disease name")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Raw model probability score")
    normalized_risk: float = Field(..., ge=0.0, le=1.0, description="Normalized risk score")
    risk_percentage: float = Field(..., ge=0.0, le=100.0, description="Risk score percentage")
    risk_level: Literal["low", "moderate", "high", "very_high"] = Field(..., description="LifeOS project risk band")
    threshold: float = Field(..., description="Model operating threshold")
    model: str = Field(..., description="Model architecture used")


class RiskFusionResponse(BaseModel):
    overall_risk_score: float = Field(..., ge=0.0, le=1.0, description="Weighted average normalized risk score")
    overall_risk_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall risk score percentage")
    overall_risk_level: Literal["low", "moderate", "high", "very_high"] = Field(..., description="Overall LifeOS project risk band")
    overall_health_score: int = Field(..., ge=0, le=100, description="Composite LifeOS Health Score (100 - overall_risk_percentage)")
    top_priority_disease: str = Field(..., description="Identifier of highest risk disease")
    top_priority_display_name: str = Field(..., description="Human readable name of top priority disease")
    top_priority_score: float = Field(..., ge=0.0, le=1.0, description="Score of top priority disease")
    disease_ranking: list[RankedDiseaseItem] = Field(..., description="Prioritized ranking of all evaluated diseases")
    high_risk_diseases: list[str] = Field(..., description="List of diseases in high or very_high risk bands")
    very_high_risk_diseases: list[str] = Field(..., description="List of diseases in very_high risk band")
    multiple_high_risk: bool = Field(..., description="True if 2 or more diseases are high/very_high risk")
    multiple_very_high_risk: bool = Field(..., description="True if 2 or more diseases are very_high risk")
    top_contributors_by_disease: dict[str, list[dict[str, Any]]] = Field(..., description="SHAP feature attributions grouped by disease")
    available_diseases_count: int = Field(..., description="Count of successfully fused disease models")
    missing_diseases: list[str] = Field(..., description="List of diseases unavailable or missing from request")
    disclaimer: str = Field(
        "LifeOS risk scores and priority rankings are project-level screening estimates derived from individual machine-learning models. They do not constitute a clinical medical diagnosis.",
        description="Clinical disclaimer notice"
    )
