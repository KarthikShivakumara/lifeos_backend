from app.schemas.nutrition import (
    DailyNutritionAggregationRequest,
    MealCalculationRequest,
    MealItemInput,
)
from app.services.nutrition_service import nutrition_service
from app.services.risk_fusion_service import DEFAULT_DISEASE_WEIGHTS


def test_nutrition_to_wellness_signal_conversion():
    all_keys = list(nutrition_service.food_db.keys())
    item_id = all_keys[0]

    meal = nutrition_service.calculate_meal_nutrition(
        MealCalculationRequest(meal_type="lunch", items=[MealItemInput(food_id=item_id, quantity_g=150.0)])
    )
    daily_req = DailyNutritionAggregationRequest(meals=[meal], user_body_weight_kg=75.0)

    wellness_sig = nutrition_service.to_wellness_signal(daily_req)

    assert wellness_sig.domain == "nutrition"
    assert 0.0 <= wellness_sig.score <= 1.0
    assert "nutrition_wellness" in wellness_sig.status
    assert "calories_kcal" in wellness_sig.metadata


def test_layer_a_risk_fusion_remains_frozen_and_uncontaminated_by_nutrition():
    weights = DEFAULT_DISEASE_WEIGHTS
    assert weights["heart"] == 0.25
    assert weights["diabetes"] == 0.25
    assert weights["hypertension"] == 0.25
    assert weights["obesity"] == 0.25
    assert "nutrition" not in weights, "Nutrition MUST NOT be added to Layer A Risk Fusion weights!"
