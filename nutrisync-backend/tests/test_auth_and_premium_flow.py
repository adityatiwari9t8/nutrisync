import os
import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB_PATH = Path("/tmp/nutrisync_test.db")

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["MOCK_CV_MODE"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Base, SessionLocal, engine  # noqa: E402
from config import JWT_SECRET  # noqa: E402
from main import app  # noqa: E402
from models.user import User  # noqa: E402
from routes import pantry as pantry_route  # noqa: E402
from seed import seed_database  # noqa: E402
from services import cv_service  # noqa: E402
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


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _image_bytes(color: tuple[int, int, int] = (240, 80, 40)) -> bytes:
    image = Image.new("RGB", (96, 96), color)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_seeded_accounts_are_limited_to_free_and_premium_pair(client: TestClient):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id.asc()).all()
        assert [user.username for user in users] == ["Yash Maurya", "Aditya Tiwari"]
        assert [user.email for user in users] == ["yashmaurya@nutrisync.dev", "adityatiwari@nutrisync.dev"]
        assert [user.is_premium for user in users] == [False, True]
    finally:
        db.close()


def test_free_user_cannot_open_premium_dietitian_endpoints(client: TestClient):
    headers = _auth_headers(client, "yashmaurya@nutrisync.dev", "yash123")

    dashboard_response = client.get("/dietitian/dashboard", headers=headers)
    concierge_response = client.get("/dietitian/concierge", headers=headers)

    assert dashboard_response.status_code == 403
    assert concierge_response.status_code == 403


def test_premium_seeded_user_can_login_with_updated_credentials(client: TestClient):
    headers = _auth_headers(client, "adityatiwari@nutrisync.dev", "aditya123")

    dashboard_response = client.get("/dietitian/dashboard", headers=headers)

    assert dashboard_response.status_code == 200


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


def test_register_normalizes_email_and_username_and_supports_case_insensitive_login(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "  Case Check  ",
            "email": "CaseCheck@NutriSync.dev",
            "password": "demo123",
            "is_premium": False,
        },
    )

    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["user"]["username"] == "Case Check"
    assert register_payload["user"]["email"] == "casecheck@nutrisync.dev"

    login_response = client.post(
        "/auth/login",
        json={"email": "CASECHECK@NUTRISYNC.DEV", "password": "demo123"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "casecheck@nutrisync.dev"


def test_register_rejects_whitespace_only_username_after_trimming(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "username": "   ",
            "email": "blankname@nutrisync.dev",
            "password": "demo123",
            "is_premium": False,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Username must be at least 3 non-space characters long."


def test_malformed_token_subject_returns_401_instead_of_server_error():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        token = jwt.encode({"sub": "abc"}, JWT_SECRET, algorithm="HS256")
        response = test_client.get("/pantry/ingredients", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token."


def test_core_app_flow_smoke_test(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "flow_user",
            "email": "flow_user@nutrisync.dev",
            "password": "demo123",
            "is_premium": False,
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pantry_response = client.post(
        "/pantry/scan",
        headers=headers,
        json={"ingredients": [" Tomato ", "banana", "tomato"]},
    )
    assert pantry_response.status_code == 200
    assert pantry_response.json()["ingredients"] == ["tomato", "banana"]

    pantry_listing = client.get("/pantry/ingredients", headers=headers)
    assert pantry_listing.status_code == 200
    assert pantry_listing.json()["ingredients"] == ["banana", "tomato"]

    recommend_response = client.post(
        "/recipes/recommend",
        headers=headers,
        json={
            "ingredients": ["tomato", "banana"],
            "macro_goals": {"protein": 30, "carbs": 60, "fat": 20, "calories": 500},
        },
    )
    assert recommend_response.status_code == 200
    recipes = recommend_response.json()
    assert recipes

    recipe_id = recipes[0]["id"]
    recipe_detail = client.get(f"/recipes/{recipe_id}", headers=headers)
    assert recipe_detail.status_code == 200
    recipe_payload = recipe_detail.json()

    log_response = client.post(
        "/tracker/log",
        headers=headers,
        json={"recipe_id": recipe_id, "servings": 1.5},
    )
    assert log_response.status_code == 200

    daily_response = client.get("/tracker/daily", headers=headers)
    assert daily_response.status_code == 200
    daily_payload = daily_response.json()
    assert daily_payload["goals"] == {"protein": 30.0, "carbs": 60.0, "fat": 20.0, "calories": 500.0}
    assert len(daily_payload["meals"]) == 1
    assert daily_payload["totals"]["protein"] == round(recipe_payload["protein_g"] * 1.5, 1)
    assert daily_payload["totals"]["carbs"] == round(recipe_payload["carbs_g"] * 1.5, 1)
    assert daily_payload["totals"]["fat"] == round(recipe_payload["fat_g"] * 1.5, 1)
    assert daily_payload["totals"]["calories"] == round(recipe_payload["calories"] * 1.5, 1)

    history_response = client.get("/tracker/history?days=3", headers=headers)
    assert history_response.status_code == 200
    assert len(history_response.json()["history"]) == 3

    blocked_concierge = client.get("/dietitian/concierge", headers=headers)
    assert blocked_concierge.status_code == 403

    upgrade_response = client.post(
        "/auth/upgrade",
        headers=headers,
        json={
            "billing_cycle": "MONTHLY",
            "payment_method": "Card",
            "cardholder_name": "Flow User",
            "card_last4": "4242",
        },
    )
    assert upgrade_response.status_code == 200
    premium_headers = {"Authorization": f"Bearer {upgrade_response.json()['access_token']}"}

    concierge_response = client.get("/dietitian/concierge", headers=premium_headers)
    assert concierge_response.status_code == 200
    concierge_payload = concierge_response.json()
    assert concierge_payload["dietitian"]["next_openings"]

    session_response = client.post(
        "/dietitian/request-session",
        headers=premium_headers,
        json={
            "preferred_slot": concierge_payload["dietitian"]["next_openings"][0],
            "goal_focus": "Hit protein goals",
            "notes": "Need weekday meal help",
        },
    )
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "confirmed"

    dashboard_response = client.get("/dietitian/dashboard", headers=premium_headers)
    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["history"]
    assert dashboard_payload["meals"]


def test_cv_service_maps_detected_labels_into_pantry_ingredients(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cv_service, "MOCK_CV_MODE", False)
    monkeypatch.setattr(cv_service, "_classify_with_clip_scores", lambda image: None)
    monkeypatch.setattr(
        cv_service,
        "_classify_with_torch_labels",
        lambda image: [
            ("banana", 0.97),
            ("bell pepper", 0.84),
            ("dining table", 0.72),
            ("Granny Smith apple", 0.63),
        ],
    )

    ingredients = cv_service.detect_ingredients(image_bytes=_image_bytes())

    assert ingredients == ["banana", "bell pepper", "apple"]


def test_clip_score_selection_keeps_clear_multi_item_matches():
    ingredients = cv_service._select_clip_ingredients(
        {
            "banana": {"max": 0.98, "sum": 1.97, "hits": 2},
            "apple": {"max": 0.92, "sum": 1.84, "hits": 2},
            "tomato": {"max": 0.89, "sum": 1.79, "hits": 2},
            "bell pepper": {"max": 0.09, "sum": 0.17, "hits": 2},
        }
    )

    assert ingredients == ["banana", "apple", "tomato"]


def test_clip_score_selection_prefers_dominant_single_item_over_close_false_positives():
    ingredients = cv_service._select_clip_ingredients(
        {
            "chicken breast": {"max": 0.75, "sum": 2.11, "hits": 6},
            "turkey breast": {"max": 0.31, "sum": 1.34, "hits": 6},
            "salmon": {"max": 0.28, "sum": 0.74, "hits": 4},
        }
    )

    assert ingredients == ["chicken breast"]


def test_clip_score_selection_drops_support_ingredients_when_clear_food_match_exists():
    ingredients = cv_service._select_clip_ingredients(
        {
            "egg": {"max": 0.81, "sum": 2.36, "hits": 6},
            "sesame oil": {"max": 0.53, "sum": 1.53, "hits": 5},
            "olive oil": {"max": 0.30, "sum": 1.38, "hits": 5},
        }
    )

    assert ingredients == ["egg"]


def test_clip_score_selection_prefers_single_tofu_when_top_match_stays_consistent():
    ingredients = cv_service._select_clip_ingredients(
        {
            "tofu": {"max": 0.30, "sum": 1.46, "hits": 6},
            "semolina": {"max": 0.28, "sum": 0.91, "hits": 5},
            "chickpeas": {"max": 0.17, "sum": 0.36, "hits": 3},
        }
    )

    assert ingredients == ["tofu"]


def test_clip_score_selection_prefers_single_onion_when_one_crop_is_extremely_confident():
    ingredients = cv_service._select_clip_ingredients(
        {
            "onion": {"max": 0.84, "sum": 0.84, "hits": 1},
            "tofu": {"max": 0.27, "sum": 0.36, "hits": 2},
            "ricotta": {"max": 0.13, "sum": 0.23, "hits": 2},
        }
    )

    assert ingredients == ["onion"]


def test_pantry_scan_returns_service_unavailable_when_scanner_backend_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    headers = _auth_headers(client, "adityatiwari@nutrisync.dev", "aditya123")

    def _raise_unavailable(*args, **kwargs):
        raise cv_service.ScanBackendUnavailable(cv_service.SCAN_UNAVAILABLE_MESSAGE)

    monkeypatch.setattr(pantry_route, "detect_ingredients", _raise_unavailable)

    response = client.post(
        "/pantry/scan",
        headers=headers,
        files={"file": ("scan.jpg", _image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == cv_service.SCAN_UNAVAILABLE_MESSAGE
