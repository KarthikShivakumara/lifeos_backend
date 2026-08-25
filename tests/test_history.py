from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.history_service import history_service


client = TestClient(app)


from app.db.base import Base
from app.db.session import engine


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    history_service.clear_history()


def test_create_and_get_snapshot() -> None:
    payload = {
        "id": "snap-test-01",
        "timestamp": "2026-08-20T10:00:00Z",
        "assessment_input": {"systolic_bp": 120, "diastolic_bp": 80},
        "disease_results": {"heart": {"risk_score": 0.20}},
        "risk_fusion": {"overall_risk_score": 0.20, "overall_health_score": 80, "overall_risk_level": "low"},
        "recommendations": [],
    }

    response = client.post("/api/v1/history", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == "snap-test-01"

    get_resp = client.get("/api/v1/history/snap-test-01")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == "snap-test-01"


def test_history_list_ordering_and_deletion() -> None:
    # Create older snapshot
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-old",
            "timestamp": "2026-08-10T10:00:00Z",
            "assessment_input": {"systolic_bp": 150},
            "risk_fusion": {"overall_risk_score": 0.70},
        },
    )

    # Create newer snapshot
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-new",
            "timestamp": "2026-08-20T10:00:00Z",
            "assessment_input": {"systolic_bp": 130},
            "risk_fusion": {"overall_risk_score": 0.50},
        },
    )

    list_resp = client.get("/api/v1/history")
    assert list_resp.status_code == 200
    snaps = list_resp.json()["snapshots"]
    assert len(snaps) == 2
    assert snaps[0]["id"] == "snap-new"  # Newest first

    # Delete single snapshot
    del_resp = client.delete("/api/v1/history/snap-old")
    assert del_resp.status_code == 200

    list_after = client.get("/api/v1/history").json()
    assert len(list_after["snapshots"]) == 1
    assert list_after["snapshots"][0]["id"] == "snap-new"


def test_trend_calculation_increasing_decreasing_stable() -> None:
    # Snap 1
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-1",
            "timestamp": "2026-08-01T10:00:00Z",
            "assessment_input": {"systolic_bp": 150, "glucose": 140},
            "disease_results": {"heart": {"risk_score": 0.60}},
            "risk_fusion": {"overall_risk_score": 0.70, "overall_health_score": 30},
        },
    )

    # Snap 2 (Significant improvement)
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-2",
            "timestamp": "2026-08-15T10:00:00Z",
            "assessment_input": {"systolic_bp": 130, "glucose": 105},
            "disease_results": {"heart": {"risk_score": 0.35}},
            "risk_fusion": {"overall_risk_score": 0.40, "overall_health_score": 60},
        },
    )

    trend_resp = client.get("/api/v1/history/trends")
    assert trend_resp.status_code == 200, trend_resp.text
    t_data = trend_resp.json()

    assert t_data["total_snapshots_evaluated"] == 2
    ov_trend = t_data["risk_trends"]["overall"]
    assert ov_trend["direction"] == "decreasing"  # 0.70 -> 0.40
    assert ov_trend["absolute_change"] == -0.30

    heart_trend = t_data["risk_trends"]["heart"]
    assert heart_trend["direction"] == "decreasing"  # 0.60 -> 0.35

    # Check biomarker trends
    sbp_trend = next(b for b in t_data["biomarker_trends"] if b["metric"] == "systolic_bp")
    assert sbp_trend["direction"] == "decreasing"  # 150 -> 130


def test_trend_stability_tolerance() -> None:
    # Change of 0.01 is below tolerance 0.03 => stable
    client.post(
        "/api/v1/history",
        json={
            "id": "s1",
            "timestamp": "2026-08-01T10:00:00Z",
            "risk_fusion": {"overall_risk_score": 0.50},
        },
    )
    client.post(
        "/api/v1/history",
        json={
            "id": "s2",
            "timestamp": "2026-08-02T10:00:00Z",
            "risk_fusion": {"overall_risk_score": 0.51},  # Change = +0.01
        },
    )

    t_data = client.get("/api/v1/history/trends").json()
    assert t_data["risk_trends"]["overall"]["direction"] == "stable"


def test_clear_all_history() -> None:
    client.post("/api/v1/history", json={"id": "s1", "timestamp": "2026-08-01T10:00:00Z"})
    client.post("/api/v1/history", json={"id": "s2", "timestamp": "2026-08-02T10:00:00Z"})

    clr_resp = client.delete("/api/v1/history")
    assert clr_resp.status_code == 200
    assert clr_resp.json()["cleared_count"] == 2

    assert len(client.get("/api/v1/history").json()["snapshots"]) == 0
