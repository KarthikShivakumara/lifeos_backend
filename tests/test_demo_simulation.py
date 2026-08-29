from __future__ import annotations

import pytest
from app.services.demo_simulation_service import demo_simulation_service, SYNTHETIC_USERS


def test_synthetic_users_count():
    """Verify exactly 7 synthetic users are configured."""
    users = demo_simulation_service.list_users()
    assert len(users) == 7
    user_ids = [u["id"] for u in users]
    assert "demo-arjun-01" in user_ids
    assert "demo-priya-02" in user_ids
    assert "demo-rahul-03" in user_ids
    assert "demo-sneha-04" in user_ids
    assert "demo-vikram-05" in user_ids
    assert "demo-ananya-06" in user_ids
    assert "demo-rohan-07" in user_ids


def test_every_user_has_exactly_seven_days():
    """Verify every synthetic user has exactly 7 days of longitudinal data."""
    for user_raw in SYNTHETIC_USERS:
        days = user_raw["days"]
        assert len(days) == 7
        day_numbers = [d["day"] for d in days]
        assert day_numbers == [1, 2, 3, 4, 5, 6, 7]


def test_get_user_day_simulation():
    """Verify retrieving day 1 and day 7 simulation data for Priya."""
    priya_d1 = demo_simulation_service.get_user_day("demo-priya-02", 1)
    assert priya_d1 is not None
    assert priya_d1["sleep_hours"] == 5.2
    assert priya_d1["steps"] == 3200

    priya_d7 = demo_simulation_service.get_user_day("demo-priya-02", 7)
    assert priya_d7 is not None
    assert priya_d7["sleep_hours"] == 7.1
    assert priya_d7["steps"] == 6500


def test_generate_weekly_report():
    """Verify 7-day weekly report generation for Rohan."""
    report = demo_simulation_service.generate_weekly_report("demo-rohan-07")
    assert report is not None
    assert report["overall_trend"] == "IMPROVING"
    assert "SYNTHETIC DEMONSTRATION DATA" in report["disclaimer"]


def test_non_existent_user():
    """Verify error handling for invalid user ID."""
    assert demo_simulation_service.get_user_detail("invalid-user-id") is None
    assert demo_simulation_service.get_user_day("invalid-user-id", 1) is None
    assert demo_simulation_service.generate_weekly_report("invalid-user-id") is None
