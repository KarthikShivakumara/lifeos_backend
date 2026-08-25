from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from app.schemas.nutrition import (
    DailyNutritionAggregationRequest,
    FoodSearchResponse,
    MealCalculationRequest,
    MealCalculationResponse,
    NutritionSignal,
)
from app.services.nutrition_service import nutrition_service

router = APIRouter()


@router.get("/search", response_model=FoodSearchResponse)
def search_food_items(q: str = Query(..., min_length=1, description="Food search query"), limit: int = Query(15, ge=1, le=50)) -> Any:
    return nutrition_service.search_food(query=q, limit=limit)


@router.post("/meal", response_model=MealCalculationResponse)
def calculate_meal(request: MealCalculationRequest) -> Any:
    return nutrition_service.calculate_meal_nutrition(request)


@router.post("/daily", response_model=NutritionSignal)
def calculate_daily_nutrition(request: DailyNutritionAggregationRequest) -> Any:
    return nutrition_service.calculate_daily_nutrition(request)
