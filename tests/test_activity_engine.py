from app.schemas.activity import ActivityEngineInput
from app.services.activity import activity_engine


def test_activity_engine_optimal():
    inp = ActivityEngineInput(
        daily_steps=9500,
        very_active_minutes=25,
        fairly_active_minutes=15,
        lightly_active_minutes=180,
        sedentary_minutes=420,  # 7.0 hours
        historical_steps=[6000, 7000, 8000, 9000, 9500],
    )
    sig = activity_engine.evaluate_activity(inp)
    assert sig.domain == "activity"
    assert sig.activity_level == "optimal"
    assert sig.sedentary_risk == "low"
    assert sig.weekly_trend == "IMPROVING"
    assert sig.activity_score >= 80.0
    assert "low_daily_step_count" not in sig.recommendation_triggers


def test_activity_engine_low_activity():
    inp = ActivityEngineInput(
        daily_steps=2200,
        very_active_minutes=0,
        fairly_active_minutes=5,
        lightly_active_minutes=60,
        sedentary_minutes=720,  # 12.0 hours
        historical_steps=[5000, 4000, 3000, 2500, 2200],
    )
    sig = activity_engine.evaluate_activity(inp)
    assert sig.activity_level == "low"
    assert sig.sedentary_risk == "elevated"
    assert sig.weekly_trend == "DECLINING"
    assert sig.activity_score < 40.0
    assert "low_daily_step_count" in sig.recommendation_triggers
    assert "elevated_sedentary_time" in sig.recommendation_triggers
