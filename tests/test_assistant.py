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


def test_unauthenticated_chat_rejection() -> None:
    res = client.post("/api/v1/assistant/chat", json={"message": "Hello"})
    assert res.status_code == 401


def test_authenticated_chat_flow_and_citations() -> None:
    # 1. Register & Login
    client.post("/api/v1/auth/register", json={"full_name": "Test User", "email": "test_ai@lifeos.ai", "password": "Password123!"})
    token = client.post("/api/v1/auth/login", json={"email": "test_ai@lifeos.ai", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add health snapshot
    client.post(
        "/api/v1/history",
        json={
            "id": "snap-ai-01",
            "timestamp": "2026-08-20T10:00:00Z",
            "assessment_input": {"systolic_bp": 160},
            "disease_results": {"hypertension": {"risk_score": 0.916}},
            "risk_fusion": {"overall_risk_percentage": 84.7, "top_priority_display_name": "Hypertension"},
        },
        headers=headers,
    )

    # 3. Send query "Why is hypertension my highest priority?"
    chat_res = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Why is hypertension my highest priority?"},
        headers=headers,
    )
    assert chat_res.status_code == 200, chat_res.text
    data = chat_res.json()

    assert "conversation_id" in data
    assert "Hypertension" in data["answer"] or "hypertension" in data["answer"].lower()
    assert "disclaimer" in data
    assert len(data["citations"]) > 0

    cid = data["conversation_id"]

    # 4. Get conversation thread details
    conv_res = client.get(f"/api/v1/assistant/conversations/{cid}", headers=headers)
    assert conv_res.status_code == 200
    msgs = conv_res.json()["messages"]
    assert len(msgs) == 2  # user + assistant

    # 5. Delete conversation
    del_res = client.delete(f"/api/v1/assistant/conversations/{cid}", headers=headers)
    assert del_res.status_code == 200
