from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_conversation_user_isolation() -> None:
    # 1. Register User A
    client.post("/api/v1/auth/register", json={"full_name": "User A", "email": "usera_ai@lifeos.ai", "password": "Password123!"})
    token_a = client.post("/api/v1/auth/login", json={"email": "usera_ai@lifeos.ai", "password": "Password123!"}).json()["access_token"]

    # 2. Register User B
    client.post("/api/v1/auth/register", json={"full_name": "User B", "email": "userb_ai@lifeos.ai", "password": "Password123!"})
    token_b = client.post("/api/v1/auth/login", json={"email": "userb_ai@lifeos.ai", "password": "Password123!"}).json()["access_token"]

    # 3. User A chats with assistant -> Conversation Created
    chat_res = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Why is hypertension my top priority?"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert chat_res.status_code == 200, chat_res.text
    conv_id = chat_res.json()["conversation_id"]

    # 4. User A list conversations -> 1 conversation
    list_a = client.get("/api/v1/assistant/conversations", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == conv_id

    # 5. User B list conversations -> 0 conversations (Isolated!)
    list_b = client.get("/api/v1/assistant/conversations", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(list_b) == 0

    # 6. User B direct access attempt -> 404
    get_cross = client.get(f"/api/v1/assistant/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_cross.status_code == 404

    # 7. User B deletion attempt -> 404
    del_cross = client.delete(f"/api/v1/assistant/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_cross.status_code == 404
