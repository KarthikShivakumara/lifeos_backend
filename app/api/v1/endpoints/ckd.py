from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.ckd import (
    CKDExplanationResponse,
    CKDPredictionRequest,
    CKDPredictionResponse,
)
from app.services.ckd_model_service import CKDModelService

router = APIRouter(tags=["Chronic Kidney Disease Assessment"])
ckd_service = CKDModelService.get_instance()


@router.post(
    "/predict/ckd",
    response_model=CKDPredictionResponse,
    summary="Predict Chronic Kidney Disease Risk Score",
    description="Evaluates CKD risk score from clinical inputs using calibrated XGBoost.",
)
def predict_ckd(req: CKDPredictionRequest) -> CKDPredictionResponse:
    try:
        return ckd_service.predict(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"CKD prediction error: {str(err)}")


@router.post(
    "/explain/ckd",
    response_model=CKDExplanationResponse,
    summary="Explain CKD Risk Score via TreeSHAP",
    description="Returns feature attributions and human-readable explanations using TreeSHAP.",
)
def explain_ckd(req: CKDPredictionRequest) -> CKDExplanationResponse:
    try:
        return ckd_service.explain(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"CKD explanation error: {str(err)}")


@router.get(
    "/health/ckd",
    summary="CKD Service Health Check",
    description="Returns CKD model artifact loading status.",
)
def ckd_health_check() -> dict[str, Any]:
    return {
        "status": "healthy" if ckd_service.model_loaded else "unhealthy",
        "disease": "ckd",
        "model_loaded": ckd_service.model_loaded,
        "operating_threshold": ckd_service.operating_threshold,
    }
