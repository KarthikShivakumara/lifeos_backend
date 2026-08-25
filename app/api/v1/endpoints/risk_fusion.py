from __future__ import annotations

from fastapi import APIRouter

from app.schemas.risk_fusion import RiskFusionRequest, RiskFusionResponse
from app.services.risk_fusion_service import risk_fusion_service


router = APIRouter()


@router.post("/risk/fusion", response_model=RiskFusionResponse, summary="Fuse 4 Disease Models into Unified Risk Summary")
def fuse_disease_risks(payload: RiskFusionRequest) -> RiskFusionResponse:
    """Fuse predictions from Heart, Diabetes, Hypertension, and Obesity models into a unified Risk Summary."""
    return risk_fusion_service.fuse_risks(payload)
