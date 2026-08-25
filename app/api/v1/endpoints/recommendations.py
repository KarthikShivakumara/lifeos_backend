from __future__ import annotations

from fastapi import APIRouter

from app.schemas.recommendation import RecommendationEngineResponse, RecommendationRequest
from app.services.recommendation_service import recommendation_service


router = APIRouter()


@router.post("/recommendations", response_model=RecommendationEngineResponse, summary="Generate Personalized Health Recommendations")
def generate_recommendations(payload: RecommendationRequest) -> RecommendationEngineResponse:
    """Generate prioritized, explainable, deduplicated health recommendations based on assessment inputs and model risk outputs."""
    return recommendation_service.generate_recommendations(payload)
