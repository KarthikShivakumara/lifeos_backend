from __future__ import annotations

from fastapi import APIRouter

from app.schemas.diabetes import (
    DiabetesExplanationResponse,
    DiabetesHealthCheckResponse,
    DiabetesPredictionRequest,
    DiabetesPredictionResponse,
)
from app.services.diabetes_model_service import diabetes_service


router = APIRouter()


@router.post("/predict/diabetes", response_model=DiabetesPredictionResponse, summary="Predict Diabetes Risk")
def predict_diabetes(payload: DiabetesPredictionRequest) -> DiabetesPredictionResponse:
    """Predict Diabetes risk score using calibrated LightGBM model (threshold = 0.70)."""
    return diabetes_service.predict(payload)


@router.post("/explain/diabetes", response_model=DiabetesExplanationResponse, summary="Explain Diabetes Risk Prediction")
def explain_diabetes(payload: DiabetesPredictionRequest) -> DiabetesExplanationResponse:
    """Explain Diabetes risk score prediction using TreeSHAP feature attributions."""
    return diabetes_service.explain(payload)


@router.get("/health/diabetes", response_model=DiabetesHealthCheckResponse, summary="Diabetes Model Health Status")
def diabetes_health() -> DiabetesHealthCheckResponse:
    """Check Diabetes model service status and version."""
    return diabetes_service.get_health_status()
