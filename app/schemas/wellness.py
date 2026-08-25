from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WellnessFactor(BaseModel):
    feature: str = Field(..., description="Feature name")
    contribution: float = Field(..., description="Feature attribution score")
    direction: Literal["increases_risk", "decreases_risk"] = Field(..., description="Impact direction")
    human_readable: str = Field(..., description="Human-readable explanation")


class WellnessSignal(BaseModel):
    domain: Literal["sleep", "stress", "activity", "nutrition"] = Field(..., description="Wellness domain")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized wellness index score (0.0 to 1.0)")
    level: Literal["low", "moderate", "elevated", "optimal"] = Field(..., description="Qualitative wellness risk level")
    status: str = Field(..., description="Domain-specific status string")
    top_factors: list[WellnessFactor] = Field(default_factory=list, description="Primary contributing factors")
    source: str = Field(..., description="Generating model or rule engine source")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Domain-specific metadata")
