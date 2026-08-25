from __future__ import annotations

from app.ai.context_builder import context_builder
from app.db.base import Base
from app.db.session import engine
from app.services.history_service import history_service


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    history_service.clear_history()


def test_context_builder_empty_user() -> None:
    ctx = context_builder.build_user_context("user-empty-123")
    assert ctx.has_assessment is False
    assert "No completed health assessment" in ctx.formatted_context_str


def test_context_builder_with_snapshot_and_trends() -> None:
    # 1. Create baseline snapshot
    history_service.create_snapshot(
        assessment_input={"systolic_bp": 160, "glucose": 180},
        disease_results={"hypertension": {"risk_score": 0.916}},
        risk_fusion={"overall_risk_score": 0.847, "overall_risk_percentage": 84.7, "overall_health_score": 15, "overall_risk_level": "very_high", "top_priority_display_name": "Hypertension"},
        recommendations=[{"title": "Monitor BP"}],
        custom_timestamp="2026-08-01T10:00:00Z",
        user_id="user-ctx-99",
    )

    # 2. Create follow-up snapshot
    history_service.create_snapshot(
        assessment_input={"systolic_bp": 130, "glucose": 105},
        disease_results={"hypertension": {"risk_score": 0.35}},
        risk_fusion={"overall_risk_score": 0.35, "overall_risk_percentage": 35.0, "overall_health_score": 65, "overall_risk_level": "moderate", "top_priority_display_name": "Hypertension"},
        recommendations=[{"title": "Maintain Physical Activity"}],
        custom_timestamp="2026-08-20T10:00:00Z",
        user_id="user-ctx-99",
    )

    ctx = context_builder.build_user_context("user-ctx-99")
    assert ctx.has_assessment is True
    assert ctx.overall_risk_percentage == 35.0
    assert ctx.top_priority_disease == "Hypertension"
    assert "Trend Observation:" in ctx.formatted_context_str
    assert "DECREASING" in ctx.formatted_context_str
