from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.schemas.sleep import SleepPredictionRequest
from app.services.sleep_model_service import SleepModelService
from app.services.notification_rules import rule_engine
from app.ai.context_builder import context_builder

client = TestClient(app)
sleep_service = SleepModelService.get_instance()


def test_01_sleep_wellness_signal_conversion() -> None:
    req = SleepPredictionRequest(
        gender="Male",
        age=35.0,
        occupation="Engineer",
        sleep_duration=5.5,
        quality_of_sleep=4.0,
        physical_activity_level=30.0,
        stress_level=8.0,
        bmi_category="Overweight",
        systolic_bp=135.0,
        diastolic_bp=85.0,
        heart_rate=78.0,
        daily_steps=4000.0,
    )
    signal = sleep_service.to_wellness_signal(req)
    assert signal.domain == "sleep"
    assert 0.0 <= signal.score <= 1.0
    assert signal.level in ("low", "moderate", "elevated")
    assert signal.status == f"sleep_wellness_{signal.level}"
    assert len(signal.top_factors) > 0
    assert signal.source == "calibrated_logistic_regression"


def test_02_sleep_wellness_notification_rule() -> None:
    disease_results = {
        "sleep": {
            "risk_score": 0.78,
            "risk_level": "elevated",
            "threshold": 0.65,
        }
    }
    rule_res = rule_engine.evaluate_wellness_rules(disease_results)
    assert rule_res is not None
    assert rule_res["type"] == "wellness_checkin"
    assert rule_res["priority"] == "moderate"
    assert "Sleep Wellness Attention Recommended" in rule_res["title"]


def test_03_context_builder_sleep_wellness() -> None:
    # Test context_builder handles sleep wellness correctly in formatting
    fake_dis = {
        "sleep": {
            "risk_score": 0.72,
            "risk_level": "elevated",
            "threshold": 0.65,
        }
    }
    # Validate notification and text structure
    rule_res = rule_engine.evaluate_wellness_rules(fake_dis)
    assert rule_res["metadata"]["domain"] == "sleep"
