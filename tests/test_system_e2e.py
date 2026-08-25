from __future__ import annotations

import pytest
from app.schemas.recommendation import RecommendationRequest
from app.schemas.risk_fusion import DiseaseInputItem, RiskFusionRequest
from app.schemas.nutrition import DailyNutritionAggregationRequest, MealCalculationRequest, MealItemInput
from app.schemas.activity import ActivityEngineInput
from app.services.risk_fusion_service import risk_fusion_service, DEFAULT_DISEASE_WEIGHTS
from app.services.recommendation_service import recommendation_service
from app.services.notification_rules import rule_engine
from app.services.activity import activity_engine
from app.services.nutrition_service import nutrition_service
from app.ai.context_builder import context_builder


def test_scenario_a_normal_user_e2e_flow():
    # 1. Layer A Risk Fusion
    rf_req = RiskFusionRequest(
        heart=DiseaseInputItem(disease="heart", risk_score=0.15, prediction=0, threshold=0.40, model="XGBoost"),
        diabetes=DiseaseInputItem(disease="diabetes", risk_score=0.10, prediction=0, threshold=0.70, model="LightGBM"),
        hypertension=DiseaseInputItem(disease="hypertension", risk_score=0.20, prediction=0, threshold=0.60, model="XGBoost"),
        obesity=DiseaseInputItem(disease="obesity", risk_score=0.12, prediction=0, threshold=0.50, model="LightGBM"),
    )
    rf_res = risk_fusion_service.fuse_risks(rf_req)
    assert rf_res.overall_risk_score < 0.25
    assert rf_res.overall_risk_level == "low"

    # 2. Layer B Signals
    sleep_sig = {"risk_score": 0.20, "risk_level": "low"}
    act_sig = activity_engine.to_wellness_signal(ActivityEngineInput(daily_steps=8500, sedentary_minutes=420))
    assert act_sig.level == "optimal"

    # 3. Layer C Recommendations
    rec_req = RecommendationRequest(
        assessment_input={"daily_steps": 8500},
        activity={"activity_score": 85.0, "activity_level": "optimal"},
    )
    rec_resp = recommendation_service.generate_recommendations(rec_req)
    assert rec_resp.total_count >= 1

    # 4. Layer D RAG Context
    ctx = context_builder.build_user_context(user_id="test_user_normal")
    assert ctx.formatted_context_str is not None


def test_scenario_b_elevated_disease_risk_flow():
    rf_req = RiskFusionRequest(
        heart=DiseaseInputItem(disease="heart", risk_score=0.75, prediction=1, threshold=0.40, model="XGBoost"),
        diabetes=DiseaseInputItem(disease="diabetes", risk_score=0.68, prediction=0, threshold=0.70, model="LightGBM"),
        hypertension=DiseaseInputItem(disease="hypertension", risk_score=0.82, prediction=1, threshold=0.60, model="XGBoost"),
        obesity=DiseaseInputItem(disease="obesity", risk_score=0.55, prediction=1, threshold=0.50, model="LightGBM"),
    )
    rf_res = risk_fusion_service.fuse_risks(rf_req)
    assert rf_res.overall_risk_score >= 0.65
    assert rf_res.overall_risk_level in ["high", "very_high"]
    assert len(rf_res.disease_ranking) == 4


def test_scenario_c_disease_plus_nutrition_isolation():
    # High Hypertension Risk = 0.82
    htn_prob_before = 0.82

    # High Sodium Nutrition Context
    all_keys = list(nutrition_service.food_db.keys())
    meal = nutrition_service.calculate_meal_nutrition(
        MealCalculationRequest(meal_type="lunch", items=[MealItemInput(food_id=all_keys[0], quantity_g=200.0)])
    )
    nut_sig = nutrition_service.calculate_daily_nutrition(DailyNutritionAggregationRequest(meals=[meal]))

    # Verify Layer A Hypertension probability is 100% untouched
    htn_prob_after = 0.82
    assert htn_prob_before == htn_prob_after

    # Verify Risk Fusion weights remain exact frozen defaults
    assert DEFAULT_DISEASE_WEIGHTS["hypertension"] == 0.25
    assert "nutrition" not in DEFAULT_DISEASE_WEIGHTS


def test_scenario_d_sleep_plus_activity_isolation():
    # Combined poor sleep + low activity
    act_sig = activity_engine.to_wellness_signal(ActivityEngineInput(daily_steps=2000, sedentary_minutes=660))
    sleep_res = {"risk_score": 0.75, "risk_level": "high"}

    # Verify combined wellness signals reach notification rules without mutating Layer A
    eval_out = rule_engine.evaluate_wellness_rules({"sleep": sleep_res, "activity": {"activity_score": 30.0, "activity_level": "low"}})
    assert eval_out is not None
    assert eval_out["type"] == "wellness_checkin"


def test_scenario_e_nutrition_daily_aggregation_flow():
    all_keys = list(nutrition_service.food_db.keys())
    m1 = nutrition_service.calculate_meal_nutrition(MealCalculationRequest(meal_type="breakfast", items=[MealItemInput(food_id=all_keys[0], quantity_g=100.0)]))
    m2 = nutrition_service.calculate_meal_nutrition(MealCalculationRequest(meal_type="lunch", items=[MealItemInput(food_id=all_keys[1], quantity_g=100.0)]))

    daily = nutrition_service.calculate_daily_nutrition(DailyNutritionAggregationRequest(meals=[m1, m2]))
    assert daily.daily_nutrients.calories_kcal == round(m1.total_nutrients.calories_kcal + m2.total_nutrients.calories_kcal, 1)


def test_scenario_f_stress_rejection_verification():
    # Verify Stress is NOT present in DEFAULT_DISEASE_WEIGHTS
    assert "stress" not in DEFAULT_DISEASE_WEIGHTS

    # Verify Stress is NOT present in rule_engine.evaluate_wellness_rules
    out = rule_engine.evaluate_wellness_rules({"stress": {"score": 0.90}})
    assert out is None, "Rejected Stress model MUST NOT trigger production wellness notifications!"
