from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.services.history_service import history_service

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    history_service.clear_history()


def test_user_health_history_isolation() -> None:
    # 1. Register User A
    user_a_res = client.post("/api/v1/auth/register", json={"full_name": "User A", "email": "usera@lifeos.ai", "password": "Password123!"})
    assert user_a_res.status_code == 200
    token_a = client.post("/api/v1/auth/login", json={"email": "usera@lifeos.ai", "password": "Password123!"}).json()["access_token"]

    # 2. Register User B
    user_b_res = client.post("/api/v1/auth/register", json={"full_name": "User B", "email": "userb@lifeos.ai", "password": "Password123!"})
    assert user_b_res.status_code == 200
    token_b = client.post("/api/v1/auth/login", json={"email": "userb@lifeos.ai", "password": "Password123!"}).json()["access_token"]

    # 3. User A creates snapshot
    snap_payload = {
        "id": "snap-usera-01",
        "timestamp": "2026-08-20T10:00:00Z",
        "assessment_input": {"systolic_bp": 140},
        "risk_fusion": {"overall_risk_score": 0.50},
    }
    create_res = client.post("/api/v1/history", json=snap_payload, headers={"Authorization": f"Bearer {token_a}"})
    assert create_res.status_code == 200

    # 4. User A fetches history -> 1 snapshot
    list_a = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert list_a["total_count"] == 1
    assert list_a["snapshots"][0]["id"] == "snap-usera-01"

    # 5. User B fetches history -> 0 snapshots (User A's data is isolated!)
    list_b = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert list_b["total_count"] == 0

    # 6. User B attempts to access User A's snapshot directly -> 404 / Forbidden
    get_cross = client.get("/api/v1/history/snap-usera-01", headers={"Authorization": f"Bearer {token_b}"})
    assert get_cross.status_code == 404

    # 7. User B attempts to delete User A's snapshot -> 404 / Rejected
    del_cross = client.delete("/api/v1/history/snap-usera-01", headers={"Authorization": f"Bearer {token_b}"})
    assert del_cross.status_code == 404

    # 8. Verify User A's snapshot is untouched
    list_a_after = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert list_a_after["total_count"] == 1
