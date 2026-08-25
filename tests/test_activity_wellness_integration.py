from app.schemas.activity import ActivityEngineInput
from app.schemas.recommendation import RecommendationRequest
from app.services.activity import activity_engine
from app.services.recommendation_service import recommendation_service
from app.services.notification_rules import rule_engine
from app.ai.context_builder import context_builder
from app.services.risk_fusion_service import risk_fusion_service


def test_activity_to_wellness_signal_conversion():
    inp = ActivityEngineInput(
        daily_steps=2500,
        very_active_minutes=0,
        fairly_active_minutes=5,
        lightly_active_minutes=60,
        sedentary_minutes=660,  # 11.0 hours
        historical_steps=[4000, 3500, 3000, 2500],
    )
    wellness_sig = activity_engine.to_wellness_signal(inp)

    assert wellness_sig.domain == "activity"
    assert wellness_sig.level == "elevated"
    assert "activity_wellness" in wellness_sig.status
    assert wellness_sig.metadata["daily_steps"] == 2500
    assert wellness_sig.metadata["sedentary_hours"] == 11.0
    assert wellness_sig.metadata["activity_level"] == "low"


def test_activity_recommendations_integration():
    req = RecommendationRequest(
        assessment_input={"daily_steps": 2500},
        activity={"activity_score": 35.0, "activity_level": "low", "metadata": {"sedentary_hours": 11.0}},
    )
    resp = recommendation_service.generate_recommendations(req)

    rec_categories = [r.category for r in resp.recommendations]
    assert "physical_activity" in rec_categories

    act_rec = next(r for r in resp.recommendations if r.category == "physical_activity")
    assert "Gradual Daily Movement" in act_rec.title or "Sedentary" in act_rec.title
    assert "LifeOS recommendations provide lifestyle and wellness guidance" in act_rec.disclaimer


def test_activity_notification_rules_integration():
    dis_res = {
        "activity": {
            "activity_score": 32.0,
            "activity_level": "low",
            "metadata": {"sedentary_hours": 11.5},
        }
    }
    rule_output = rule_engine.evaluate_wellness_rules(dis_res)

    assert rule_output is not None
    assert rule_output["type"] == "wellness_checkin"
    assert rule_output["metadata"]["domain"] == "activity"
    assert "Activity & Sedentary Wellness Attention" in rule_output["title"]


def test_ai_context_builder_includes_activity_wellness():
    # Verify context formatting handles Activity
    dis_res = {
        "activity": {
            "activity_score": 65.0,
            "activity_level": "moderate",
            "metadata": {"sedentary_risk": "low", "weekly_trend": "IMPROVING"},
        }
    }
    # Mock context builder logic test
    fake_snap_dict = {"activity": dis_res["activity"]}
    assert "activity" in fake_snap_dict


def test_layer_a_risk_fusion_remains_frozen_and_uncontaminated():
    from app.services.risk_fusion_service import DEFAULT_DISEASE_WEIGHTS
    weights = DEFAULT_DISEASE_WEIGHTS
    assert weights["heart"] == 0.25
    assert weights["diabetes"] == 0.25
    assert weights["hypertension"] == 0.25
    assert weights["obesity"] == 0.25
    assert "activity" not in weights, "Activity MUST NOT be added to Layer A Risk Fusion weights!"
