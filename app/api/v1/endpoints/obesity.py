from __future__ import annotations

from fastapi import APIRouter

from app.schemas.obesity import (
    ObesityExplanationResponse,
    ObesityHealthCheckResponse,
    ObesityPredictionRequest,
    ObesityPredictionResponse,
)
from app.services.obesity_model_service import obesity_service


router = APIRouter()


@router.post("/predict/obesity", response_model=ObesityPredictionResponse, summary="Predict Obesity Risk")
def predict_obesity(payload: ObesityPredictionRequest) -> ObesityPredictionResponse:
    """Predict Obesity lifestyle risk score using calibrated LightGBM model (threshold = 0.50)."""
    return obesity_service.predict(payload)


@router.post("/explain/obesity", response_model=ObesityExplanationResponse, summary="Explain Obesity Risk Prediction")
def explain_obesity(payload: ObesityPredictionRequest) -> ObesityExplanationResponse:
    """Explain Obesity risk score prediction using TreeSHAP feature attributions."""
    return obesity_service.explain(payload)


@router.get("/health/obesity", response_model=ObesityHealthCheckResponse, summary="Obesity Model Health Status")
def obesity_health() -> ObesityHealthCheckResponse:
    """Check Obesity model service status and version."""
    return obesity_service.get_health_status()
