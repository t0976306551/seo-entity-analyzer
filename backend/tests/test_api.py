# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.auth import get_current_user

# Mock get_supabase at the module level before importing app,
# so the singleton in database.py never tries a real connection.
mock_supabase = MagicMock()
mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
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
    local_mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
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


def test_analyze_keyword_too_short():
    """Keyword shorter than 2 chars should return 400"""
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        response = client.post("/analyze", json={"keyword": "a"}, headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 400


def test_analyze_keyword_too_long():
    """Keyword longer than 200 chars should return 400"""
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        response = client.post("/analyze", json={"keyword": "a" * 201}, headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 400


def test_register_missing_email():
    """Register with missing email field should return 422"""
    response = client.post("/auth/register", json={"password": "password123"})
    assert response.status_code == 422


def test_register_missing_password():
    """Register with missing password field should return 422"""
    response = client.post("/auth/register", json={"email": "test@test.com"})
    assert response.status_code == 422


def test_analyze_keyword_boundary_min():
    """剛好 2 個字元的 keyword 應回傳 202（不被拒絕）"""
    from app.auth import get_current_user
    # 設定有效的 sheet mock
    local_mock_db = MagicMock()
    local_mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "sheet_id": "test_sheet_id",
        "sheet_url": "https://docs.google.com/test",
        "status": "active",
    }
    local_mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        with patch("app.routers.analyze.get_supabase", return_value=local_mock_db):
            with patch("app.services.job_runner.run_analysis_job"):
                response = client.post(
                    "/analyze",
                    json={"keyword": "ab"},
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 202


def test_analyze_keyword_boundary_max():
    """剛好 200 個字元的 keyword 應回傳 202（不被拒絕）"""
    from app.auth import get_current_user
    local_mock_db = MagicMock()
    local_mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "sheet_id": "test_sheet_id",
        "sheet_url": "https://docs.google.com/test",
        "status": "active",
    }
    local_mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        with patch("app.routers.analyze.get_supabase", return_value=local_mock_db):
            with patch("app.services.job_runner.run_analysis_job"):
                response = client.post(
                    "/analyze",
                    json={"keyword": "a" * 200},
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 202


def test_analyze_whitespace_keyword_returns_400():
    """純空白的 keyword 在 strip 後應被視為 empty 而回傳 400"""
    from app.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        response = client.post(
            "/analyze",
            json={"keyword": "   "},
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 400


def test_analyze_sheet_not_ready_returns_400():
    """user_sheets status 不是 active 時應回傳 400"""
    from app.auth import get_current_user
    local_mock_db = MagicMock()
    local_mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "sheet_id": "",
        "sheet_url": "",
        "status": "pending",
    }
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        with patch("app.routers.analyze.get_supabase", return_value=local_mock_db):
            response = client.post(
                "/analyze",
                json={"keyword": "4G吃到飽"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 400
    assert "not ready" in response.json()["detail"]


def test_job_status_not_found_returns_404():
    """不存在的 job_id 應回傳 404"""
    from app.auth import get_current_user
    local_mock_db = MagicMock()
    local_mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-uuid", "email": "test@test.com"}
    try:
        with patch("app.routers.analyze.get_supabase", return_value=local_mock_db):
            response = client.get(
                "/job/nonexistent-job-id",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 404
