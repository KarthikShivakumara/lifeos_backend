from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.db.session import engine
from app.main import RATE_LIMIT_STORE, app

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    RATE_LIMIT_STORE.clear()


def test_production_secret_key_validation() -> None:
    # 1. Weak secret key in production mode raises ValueError
    bad_settings = Settings(
        environment="production",
        secret_key="change-me",
    )
    with pytest.raises(ValueError, match="Secret key must be a secure random string"):
        bad_settings.validate_production_secrets()

    # 2. Wildcard CORS in production mode raises ValueError
    wildcard_settings = Settings(
        environment="production",
        secret_key="a_very_long_secure_secret_key_for_lifeos_production_environment_2026",
        cors_origins="*",
    )
    with pytest.raises(ValueError, match="Wildcard CORS origin '\*' is strictly prohibited"):
        wildcard_settings.validate_production_secrets()

    # 3. Valid production settings pass validation
    valid_settings = Settings(
        environment="production",
        secret_key="a_very_long_secure_secret_key_for_lifeos_production_environment_2026",
        cors_origins="https://lifeos.health",
    )
    valid_settings.validate_production_secrets()
    assert valid_settings.is_production is True


def test_reverse_proxy_x_forwarded_for_rate_limiting() -> None:
    # Simulate requests behind reverse proxy with X-Forwarded-For header
    proxy_ip = "203.0.113.195"
    headers = {"X-Forwarded-For": f"{proxy_ip}, 10.0.0.1"}

    for _ in range(5):
        client.get("/health", headers=headers)

    assert proxy_ip in RATE_LIMIT_STORE
    assert len(RATE_LIMIT_STORE[proxy_ip]) == 5
