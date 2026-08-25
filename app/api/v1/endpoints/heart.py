from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.heart import (
    HealthCheckResponse,
    HeartExplanationResponse,
    HeartPredictionRequest,
    HeartPredictionResponse,
)
from app.services.heart_model_service import heart_service


router = APIRouter(tags=["Heart Disease Risk Assessment"])


@router.post(
    "/predict/heart",
    response_model=HeartPredictionResponse,
    summary="Predict Heart Disease Risk Score",
    description="Evaluates Heart Disease risk score from 12 input features using calibrated XGBoost.",
)
def predict_heart(req: HeartPredictionRequest) -> HeartPredictionResponse:
    try:
        return heart_service.predict(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Heart disease prediction error: {str(err)}")


@router.post(
    "/explain/heart",
    response_model=HeartExplanationResponse,
    summary="Explain Heart Disease Risk Score via SHAP",
    description="Returns top 5 feature risk attributions and human-readable explanations using TreeSHAP.",
)
def explain_heart(req: HeartPredictionRequest) -> HeartExplanationResponse:
    try:
        return heart_service.explain(req)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Heart disease explanation error: {str(err)}")


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Heart Model Service Health Check",
    description="Returns system status and model loading state.",
)
def heart_health() -> HealthCheckResponse:
    return heart_service.get_health_status()
