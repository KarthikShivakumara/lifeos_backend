from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.base  # noqa: F401
from app.core.deps import get_current_user, get_db
from app.db.session import Base
from app.main import app
from app.models.user import User


@pytest.fixture(scope="module")
def e2e_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def e2e_db(e2e_engine):
    SessionLocal = sessionmaker(bind=e2e_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_user(e2e_db):

    user = User(
        id="user-scenario-g-01",
        email="scenariog@lifeos.org",
        password_hash="secure_password",
        full_name="Scenario G User",
    )
    e2e_db.add(user)
    e2e_db.commit()
    e2e_db.refresh(user)
    return user



@pytest.fixture
def client(e2e_db, mock_user):
    def override_get_db():
        yield e2e_db

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_scenario_g_stress_lifecycle_and_layer_isolation(client: TestClient):
    """
    Scenario G: End-to-End Stress Intelligence Lifecycle
    1. Initial state: GET /api/v1/stress/current returns clean empty state.
    2. Record check-in: POST /api/v1/stress/checkins.
    3. Verify current status: GET /api/v1/stress/current reflects new index.
    4. Verify history: GET /api/v1/stress/history contains record.
    5. Record 3 additional check-ins to build trajectory.
    6. Verify trends: GET /api/v1/stress/trends?days=7.
    7. Verify summary: GET /api/v1/stress/summary.
    8. Verify recommendations: GET /api/v1/stress/recommendations.
    9. Layer A Isolation Check: Ensure clinical predictions endpoint (/api/v1/predictions/heart)
       operates with zero interference from stress data.
    """
    # 1. Initial status
    res = client.get("/api/v1/stress/current")
    assert res.status_code == 200
    data = res.json()
    assert data["trend"] == "INSUFFICIENT_DATA"
    assert data["is_diagnostic"] is False

    # 2. Record first check-in
    payload = {
        "perceived_stress": 7,
        "overwhelm": 6,
        "difficulty_relaxing": 5,
        "mood": 5,
        "energy": 4,
        "notes": "Tight project deadline today",
    }
    post_res = client.post("/api/v1/stress/checkins", json=payload)
    assert post_res.status_code == 201
    checkin = post_res.json()
    assert checkin["stress_index"] > 50.0
    assert checkin["stress_level"] in ("moderate", "high")
    assert checkin["is_diagnostic"] is False

    # 3. GET /current
    curr_res = client.get("/api/v1/stress/current")
    assert curr_res.status_code == 200
    curr_data = curr_res.json()
    assert curr_data["current_index"] == checkin["stress_index"]
    assert curr_data["latest_checkin"]["id"] == checkin["id"]

    # 4. GET /history
    hist_res = client.get("/api/v1/stress/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 1

    # 5. Record additional check-ins
    client.post("/api/v1/stress/checkins", json={"perceived_stress": 8, "overwhelm": 7})
    client.post("/api/v1/stress/checkins", json={"perceived_stress": 4, "overwhelm": 3})

    # 6. GET /trends
    tr_res = client.get("/api/v1/stress/trends?days=7")
    assert tr_res.status_code == 200
    tr_data = tr_res.json()
    assert tr_data["days_requested"] == 7
    assert len(tr_data["data_points"]) == 3
    assert tr_data["average_index"] is not None

    # 7. GET /summary
    sum_res = client.get("/api/v1/stress/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_checkins_30d"] == 3
    assert sum_data["consistency_score"] > 0

    # 8. GET /recommendations
    recs_res = client.get("/api/v1/stress/recommendations")
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) > 0
    assert "title" in recs[0]

    # 9. Verify Layer A Isolation
    # Heart disease screening endpoint operates cleanly with standard clinical inputs
    clinical_payload = {
        "age_years": 45.0,
        "sex": 1.0,
        "systolic_bp_mmHg": 120,
        "diastolic_bp_mmHg": 80.0,
        "cholesterol_ordinal": 1.0,
        "glucose_ordinal": 1.0,
        "physical_activity": 1.0,
        "smoking_status": 0.0,
    }
    heart_res = client.post("/api/v1/predict/heart", json=clinical_payload)
    assert heart_res.status_code == 200
    heart_data = heart_res.json()
    assert "prediction" in heart_data
    assert 0.0 <= heart_data["risk_score"] <= 1.0

