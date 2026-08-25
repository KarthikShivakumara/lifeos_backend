from app.schemas.nutrition import (
    DailyNutritionAggregationRequest,
    MealCalculationRequest,
    MealItemInput,
)
from app.services.nutrition_service import nutrition_service


def test_nutrition_search():
    res = nutrition_service.search_food("eggs", limit=5)
    assert res.total_results >= 1
    assert any("egg" in f.food_name.lower() for f in res.results)


def test_nutrition_indian_search():
    res = nutrition_service.search_food("chai", limit=5)
    assert res.total_results >= 1
    assert any("chai" in f.food_name.lower() for f in res.results)
    assert any(f.cultural_tag == "indian" for f in res.results)


def test_meal_calculation():
    # Pick first indexed item
    all_keys = list(nutrition_service.food_db.keys())
    assert len(all_keys) > 0, "Nutrition database should be indexed"

    item_id = all_keys[0]
    req = MealCalculationRequest(
        meal_type="breakfast",
        items=[MealItemInput(food_id=item_id, quantity_g=200.0)],  # 200g portion
    )
    resp = nutrition_service.calculate_meal_nutrition(req)

    assert resp.meal_type == "breakfast"
    assert resp.items_count == 1
    p100 = nutrition_service.food_db[item_id].nutrients_per_100g
    assert resp.total_nutrients.calories_kcal == round(p100.calories_kcal * 2.0, 1)


def test_daily_nutrition_aggregation():
    all_keys = list(nutrition_service.food_db.keys())
    item1 = all_keys[0]
    item2 = all_keys[1] if len(all_keys) > 1 else all_keys[0]

    meal1 = nutrition_service.calculate_meal_nutrition(
        MealCalculationRequest(meal_type="breakfast", items=[MealItemInput(food_id=item1, quantity_g=100.0)])
    )
    meal2 = nutrition_service.calculate_meal_nutrition(
        MealCalculationRequest(meal_type="lunch", items=[MealItemInput(food_id=item2, quantity_g=150.0)])
    )

    daily_req = DailyNutritionAggregationRequest(meals=[meal1, meal2], user_body_weight_kg=70.0)
    sig = nutrition_service.calculate_daily_nutrition(daily_req)

    assert sig.domain == "nutrition"
    assert sig.nutrition_score >= 0.0
    assert sig.dietary_quality_level in ["low", "moderate", "optimal"]
    assert "[Non-diagnostic wellness indicator]" in sig.non_diagnostic_disclaimer
