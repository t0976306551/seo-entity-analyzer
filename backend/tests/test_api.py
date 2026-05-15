# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock get_supabase at the module level before importing app,
# so the singleton in database.py never tries a real connection.
mock_supabase = MagicMock()
mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
    "sheet_id": "test_sheet_id",
    "status": "active",
}

with patch("app.database.get_supabase", return_value=mock_supabase):
    from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_USER = {"user_id": "test-uuid-1234", "email": "test@test.com"}


def _mock_get_current_user():
    """Dependency override that always returns a fake authenticated user."""
    return FAKE_USER


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_health_check():
    """GET /health should return 200 {"status": "ok"} with no auth."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_requires_auth():
    """POST /analyze without Authorization header must return 401."""
    response = client.post("/analyze", json={"keyword": "test"})
    assert response.status_code == 401


def test_history_requires_auth():
    """GET /history without Authorization header must return 401."""
    response = client.get("/history")
    assert response.status_code == 401


def test_job_status_requires_auth():
    """GET /job/<id> without Authorization header must return 401."""
    response = client.get("/job/some-job-id")
    assert response.status_code == 401


def test_analyze_empty_keyword_returns_400():
    """POST /analyze with empty keyword must return 400 when authenticated."""
    from app.auth import get_current_user
    from app.database import get_supabase

    # Build a local supabase mock that reports an active sheet
    local_mock_db = MagicMock()
    local_mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "sheet_id": "test_sheet_id",
        "status": "active",
    }

    # Override FastAPI dependency so auth passes, and patch DB so it won't call real Supabase
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    try:
        with patch("app.routers.analyze.get_supabase", return_value=local_mock_db):
            response = client.post(
                "/analyze",
                json={"keyword": ""},
                headers={"Authorization": "Bearer fake_token"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_login_missing_body():
    """POST /auth/login with missing fields should return 422 (validation error)."""
    response = client.post("/auth/login", json={})
    assert response.status_code == 422
