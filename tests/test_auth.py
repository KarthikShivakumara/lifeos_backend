from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_password_hashing_and_verification() -> None:
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding() -> None:
    token = create_access_token(subject="user-uuid-123", extra={"email": "test@lifeos.ai"})
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["email"] == "test@lifeos.ai"


def test_user_registration_and_login_flow() -> None:
    # 1. Register User
    reg_payload = {
        "full_name": "Alice Health",
        "email": "alice@lifeos.ai",
        "password": "Password123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["email"] == "alice@lifeos.ai"
    assert "id" in reg_data

    # 2. Duplicate registration rejection
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400
    assert "Email already registered" in dup_res.json()["detail"]

    # 3. Login with wrong password
    bad_login = client.post("/api/v1/auth/login", json={"email": "alice@lifeos.ai", "password": "WrongPassword"})
    assert bad_login.status_code in [400, 401]

    # 4. Login with correct credentials
    login_res = client.post("/api/v1/auth/login", json={"email": "alice@lifeos.ai", "password": "Password123!"})
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 5. Get current user via /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "alice@lifeos.ai"


def test_unauthenticated_me_request_rejection() -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
