# backend/tests/test_auth.py
import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

def test_missing_token_raises_401():
    import asyncio
    from app.auth import get_current_user
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(None))
    assert exc.value.status_code == 401

def test_invalid_token_raises_401():
    import asyncio
    from unittest.mock import patch, MagicMock
    from app.auth import get_current_user
    from fastapi import HTTPException

    mock_db = MagicMock()
    mock_db.auth.get_user.side_effect = Exception("Invalid JWT")

    with patch("app.auth.get_supabase", return_value=mock_db):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_current_user("Bearer invalid.token.here"))
    assert exc.value.status_code == 401


def test_bearer_with_no_token_raises_401():
    """Bug fix: 'Bearer' with no token part should return 401, not IndexError"""
    import asyncio
    from app.auth import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user("Bearer"))
    assert exc.value.status_code == 401

def test_non_bearer_scheme_raises_401():
    """Basic scheme other than Bearer should return 401"""
    import asyncio
    from app.auth import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user("Basic dXNlcjpwYXNz"))
    assert exc.value.status_code == 401
