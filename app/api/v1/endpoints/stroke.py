from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.stroke import (
    StrokeExplanationResponse,
    StrokePredictionRequest,
    StrokePredictionResponse,
)
from app.services.stroke_model_service import StrokeModelService

router = APIRouter(tags=["Stroke Risk Assessment"])
stroke_service = StrokeModelService.get_instance()


@router.post(
    "/predict/stroke",
    response_model=StrokePredictionResponse,
    summary="Predict Stroke Risk Score",
    description="Evaluates Stroke risk score from patient features using calibrated LightGBM.",
)
def predict_stroke(req: StrokePredictionRequest) -> StrokePredictionResponse:
    try:
        return stroke_service.predict(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Stroke prediction error: {str(err)}")


@router.post(
    "/explain/stroke",
    response_model=StrokeExplanationResponse,
    summary="Explain Stroke Risk Score via TreeSHAP",
    description="Returns feature attributions and human-readable explanations using TreeSHAP.",
)
def explain_stroke(req: StrokePredictionRequest) -> StrokeExplanationResponse:
    try:
        return stroke_service.explain(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Stroke explanation error: {str(err)}")


@router.get(
    "/health/stroke",
    summary="Stroke Service Health Check",
    description="Returns stroke model artifact loading status.",
)
def stroke_health_check() -> dict[str, Any]:
    return {
        "status": "healthy" if stroke_service.model_loaded else "unhealthy",
        "disease": "stroke",
        "model_loaded": stroke_service.model_loaded,
        "operating_threshold": stroke_service.operating_threshold,
    }
