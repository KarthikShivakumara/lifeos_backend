from __future__ import annotations

from fastapi import APIRouter

from app.schemas.hypertension import (
    HypertensionExplanationResponse,
    HypertensionHealthCheckResponse,
    HypertensionPredictionRequest,
    HypertensionPredictionResponse,
)
from app.services.hypertension_model_service import hypertension_service


router = APIRouter()


@router.post("/predict/hypertension", response_model=HypertensionPredictionResponse, summary="Predict Hypertension Risk")
def predict_hypertension(payload: HypertensionPredictionRequest) -> HypertensionPredictionResponse:
    """Predict Hypertension risk score using calibrated XGBoost model (threshold = 0.60)."""
    return hypertension_service.predict(payload)


@router.post("/explain/hypertension", response_model=HypertensionExplanationResponse, summary="Explain Hypertension Risk Prediction")
def explain_hypertension(payload: HypertensionPredictionRequest) -> HypertensionExplanationResponse:
    """Explain Hypertension risk score prediction using TreeSHAP feature attributions."""
    return hypertension_service.explain(payload)


@router.get("/health/hypertension", response_model=HypertensionHealthCheckResponse, summary="Hypertension Model Health Status")
def hypertension_health() -> HypertensionHealthCheckResponse:
    """Check Hypertension model service status and version."""
    return hypertension_service.get_health_status()
