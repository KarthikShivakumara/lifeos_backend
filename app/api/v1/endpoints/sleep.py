from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.sleep import (
    SleepExplanationResponse,
    SleepPredictionRequest,
    SleepPredictionResponse,
)
from app.services.sleep_model_service import SleepModelService

router = APIRouter(tags=["Sleep Wellness Intelligence"])
sleep_service = SleepModelService.get_instance()


@router.post(
    "/predict/sleep",
    response_model=SleepPredictionResponse,
    summary="Predict Sleep Risk Index",
    description="Evaluates Sleep risk index from lifestyle inputs using calibrated Logistic Regression.",
)
def predict_sleep(req: SleepPredictionRequest) -> SleepPredictionResponse:
    try:
        return sleep_service.predict(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Sleep prediction error: {str(err)}")


@router.post(
    "/explain/sleep",
    response_model=SleepExplanationResponse,
    summary="Explain Sleep Risk Score via SHAP/Linear Attributions",
    description="Returns feature attributions and human-readable explanations.",
)
def explain_sleep(req: SleepPredictionRequest) -> SleepExplanationResponse:
    try:
        return sleep_service.explain(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Sleep explanation error: {str(err)}")


@router.get(
    "/health/sleep",
    summary="Sleep Service Health Check",
    description="Returns Sleep model artifact loading status.",
)
def sleep_health_check() -> dict[str, Any]:
    return {
        "status": "healthy" if sleep_service.model_loaded else "unhealthy",
        "subsystem": "sleep_wellness",
        "model_loaded": sleep_service.model_loaded,
        "operating_threshold": sleep_service.operating_threshold,
    }
