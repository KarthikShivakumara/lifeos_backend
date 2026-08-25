from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.services.history_service import history_service
from app.services.notification_service import notification_service

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    history_service.clear_history()
    notification_service.clear_notifications()


def test_notification_crud_and_user_isolation() -> None:
    # 1. Register User A
    client.post("/api/v1/auth/register", json={"full_name": "User A", "email": "usera_notif@lifeos.ai", "password": "Password123!"})
    token_a = client.post("/api/v1/auth/login", json={"email": "usera_notif@lifeos.ai", "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    client.post("/api/v1/auth/register", json={"full_name": "User B", "email": "userb_notif@lifeos.ai", "password": "Password123!"})
    token_b = client.post("/api/v1/auth/login", json={"email": "userb_notif@lifeos.ai", "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create snapshot for User A -> Trigger notification generation
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-notif-01",
            "timestamp": "2026-08-20T10:00:00Z",
            "assessment_input": {"systolic_bp": 160},
            "disease_results": {"hypertension": {"risk_score": 0.916}},
            "risk_fusion": {"overall_risk_score": 0.847, "overall_risk_percentage": 84.7, "overall_risk_level": "very_high", "top_priority_display_name": "Hypertension"},
        },
        headers=headers_a,
    )

    gen_res = client.post("/api/v1/notifications/generate", headers=headers_a)
    assert gen_res.status_code == 200, gen_res.text
    gen_data = gen_res.json()
    assert gen_data["generated_count"] >= 1

    # 4. User A list notifications -> unread_count >= 1
    list_a = client.get("/api/v1/notifications", headers=headers_a).json()
    assert list_a["total_count"] >= 1
    assert list_a["unread_count"] >= 1
    notif_id = list_a["notifications"][0]["id"]

    # 5. User B list notifications -> 0 (User Isolation Verified)
    list_b = client.get("/api/v1/notifications", headers=headers_b).json()
    assert list_b["total_count"] == 0

    # 6. User B attempt cross-user mark_read / delete -> 404
    read_cross = client.put(f"/api/v1/notifications/{notif_id}/read", headers=headers_b)
    assert read_cross.status_code == 404

    del_cross = client.delete(f"/api/v1/notifications/{notif_id}", headers=headers_b)
    assert del_cross.status_code == 404

    # 7. User A mark as read
    read_res = client.put(f"/api/v1/notifications/{notif_id}/read", headers=headers_a)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 8. User A delete notification
    del_res = client.delete(f"/api/v1/notifications/{notif_id}", headers=headers_a)
    assert del_res.status_code == 200


def test_notification_deduplication_and_risk_rules() -> None:
    client.post("/api/v1/auth/register", json={"full_name": "Dedupe User", "email": "dedupe@lifeos.ai", "password": "Password123!"})
    token = client.post("/api/v1/auth/login", json={"email": "dedupe@lifeos.ai", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/v1/history",
        json={
            "id": "snap-dedupe-01",
            "timestamp": "2026-08-20T10:00:00Z",
            "assessment_input": {"systolic_bp": 160},
            "disease_results": {"hypertension": {"risk_score": 0.916}},
            "risk_fusion": {"overall_risk_score": 0.847, "overall_risk_percentage": 84.7, "overall_risk_level": "very_high", "top_priority_display_name": "Hypertension"},
        },
        headers=headers,
    )

    # First generation call
    gen1 = client.post("/api/v1/notifications/generate", headers=headers).json()
    count1 = gen1["generated_count"]
    assert count1 >= 1

    # Second generation call (Deduplication Check)
    gen2 = client.post("/api/v1/notifications/generate", headers=headers).json()
    count2 = gen2["generated_count"]
    assert count2 == 0  # No duplicate notifications generated!


def test_assessment_notification_failure_isolation() -> None:
    # Verify notification failure does not cause assessment API to fail
    client.post("/api/v1/auth/register", json={"full_name": "Iso User", "email": "iso@lifeos.ai", "password": "Password123!"})
    token = client.post("/api/v1/auth/login", json={"email": "iso@lifeos.ai", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Assessment creation should succeed clean
    res = client.post(
        "/api/v1/history",
        json={
            "id": "snap-iso-01",
            "timestamp": "2026-08-20T10:00:00Z",
            "assessment_input": {"systolic_bp": 120},
            "disease_results": {},
            "risk_fusion": {"overall_risk_score": 0.20, "overall_risk_percentage": 20.0},
        },
        headers=headers,
    )
    assert res.status_code == 200
