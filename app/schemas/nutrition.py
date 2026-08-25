from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class NutrientProfile(BaseModel):
    calories_kcal: float = Field(0.0, ge=0.0, description="Energy expenditure or intake in kcal")
    protein_g: float = Field(0.0, ge=0.0, description="Protein in grams")
    carbohydrates_g: float = Field(0.0, ge=0.0, description="Carbohydrates in grams")
    fat_g: float = Field(0.0, ge=0.0, description="Total lipids / fat in grams")
    fiber_g: float = Field(0.0, ge=0.0, description="Dietary fiber in grams")
    sugars_g: float = Field(0.0, ge=0.0, description="Free or added sugars in grams")
    sodium_mg: float = Field(0.0, ge=0.0, description="Sodium in milligrams")
    calcium_mg: float | None = Field(None, ge=0.0, description="Calcium in milligrams if available")
    iron_mg: float | None = Field(None, ge=0.0, description="Iron in milligrams if available")


class FoodItemRecord(BaseModel):
    food_id: str = Field(..., description="Unique food identifier")
    food_name: str = Field(..., description="Descriptive food item or dish name")
    category: str = Field("General", description="Food category")
    source: Literal["Indian_Food", "Daily_Food", "USDA_Foundation"] = Field(..., description="Database source provenance")
    serving_basis: str = Field("100g", description="Serving weight basis")
    nutrients_per_100g: NutrientProfile = Field(..., description="Nutrient breakdown per 100g basis")
    cultural_tag: str = Field("global", description="Cultural culinary tag: 'indian', 'western', 'global'")


class FoodSearchResponse(BaseModel):
    query: str = Field(..., description="Search query string")
    total_results: int = Field(..., description="Total matching food items")
    results: list[FoodItemRecord] = Field(default_factory=list, description="Matching food records")


class MealItemInput(BaseModel):
    food_id: str = Field(..., description="Food item ID from search")
    quantity_g: float = Field(100.0, gt=0.0, description="Quantity consumed in grams")


class MealCalculationRequest(BaseModel):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = Field("lunch", description="Meal category")
    items: list[MealItemInput] = Field(..., min_length=1, description="List of consumed food items with quantities")


class MealCalculationResponse(BaseModel):
    meal_type: str = Field(..., description="Meal category")
    total_nutrients: NutrientProfile = Field(..., description="Aggregated meal nutrient profile")
    items_count: int = Field(..., description="Number of items in meal")
    food_summary: list[dict[str, Any]] = Field(default_factory=list, description="Item breakdown")


class DailyNutritionAggregationRequest(BaseModel):
    meals: list[MealCalculationResponse] = Field(..., description="List of daily meals")
    user_body_weight_kg: float | None = Field(None, ge=30.0, le=250.0, description="Optional body weight for protein ratio")


class NutritionSignal(BaseModel):
    domain: Literal["nutrition"] = "nutrition"
    nutrition_score: float = Field(..., ge=0.0, le=100.0, description="Contextual Nutrition Score (0-100)")
    dietary_quality_level: Literal["low", "moderate", "optimal"] = Field(..., description="Qualitative dietary quality level")
    daily_nutrients: NutrientProfile = Field(..., description="Aggregated daily nutrient profile")
    recommendation_triggers: list[str] = Field(default_factory=list, description="Triggers for Layer C guidance")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Source provenance breakdown")
    source: str = "hybrid_nutrition_engine"
    non_diagnostic_disclaimer: str = Field(
        "[Non-diagnostic wellness indicator] LifeOS nutrition signals provide dietary wellness guidance and do not constitute medical prescriptions.",
        description="Mandatory non-diagnostic disclaimer"
    )
