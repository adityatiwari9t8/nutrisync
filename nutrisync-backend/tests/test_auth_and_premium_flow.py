import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB_PATH = Path("/tmp/nutrisync_test.db")

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["MOCK_CV_MODE"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from models.user import User  # noqa: E402
from seed import seed_database  # noqa: E402
from services.recommender import refresh_model  # noqa: E402


@pytest.fixture()
def client():
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_database(db)
        refresh_model(db)
    finally:
        db.close()

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def _auth_headers(client: TestClient, email: str, password: str = "demo123") -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_seeded_accounts_are_limited_to_free_and_premium_pair(client: TestClient):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id.asc()).all()
        assert [user.username for user in users] == ["Maya", "Arjun"]
        assert [user.email for user in users] == ["demo1@nutrisync.dev", "demo4@nutrisync.dev"]
        assert [user.is_premium for user in users] == [False, True]
    finally:
        db.close()


def test_free_user_cannot_open_premium_dietitian_endpoints(client: TestClient):
    headers = _auth_headers(client, "demo1@nutrisync.dev")

    dashboard_response = client.get("/dietitian/dashboard", headers=headers)
    concierge_response = client.get("/dietitian/concierge", headers=headers)

    assert dashboard_response.status_code == 403
    assert concierge_response.status_code == 403


def test_register_then_upgrade_flow_unlocks_premium(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "new_user",
            "email": "new_user@nutrisync.dev",
            "password": "demo123",
            "is_premium": True,
        },
    )

    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["user"]["is_premium"] is False

    headers = {"Authorization": f"Bearer {register_payload['access_token']}"}
    upgrade_response = client.post(
        "/auth/upgrade",
        headers=headers,
        json={
            "billing_cycle": "monthly",
            "payment_method": "card",
            "cardholder_name": "New User",
            "card_last4": "4242",
        },
    )

    assert upgrade_response.status_code == 200
    upgrade_payload = upgrade_response.json()
    assert upgrade_payload["user"]["is_premium"] is True

    dashboard_response = client.get("/dietitian/dashboard", headers={"Authorization": f"Bearer {upgrade_payload['access_token']}"})
    assert dashboard_response.status_code == 200
