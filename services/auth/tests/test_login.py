"""
Unit tests for the login service function (app.services.auth.login).

All external dependencies (user_repo, token_repo) are mocked so these tests
exercise only the business logic inside the service layer — no DB, no HTTP.

Criteria covered:
  - Successful login with a valid email returns a (user, tokens) tuple that
    contains an access_token and a refresh_token.
  - An unknown email raises InvalidCredentialsError (maps to HTTP 401).
  - A correct email but wrong password raises InvalidCredentialsError with the
    same message (no per-field leakage).
  - The access token payload contains sub, exp, and iat.
  - create_refresh_token is called with the SHA-256 hash of the raw token, not
    the raw token itself (i.e. the refresh token is stored hashed in the DB).
"""

import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsError
from app.core.security import hash_password
from app.services import auth as auth_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(email: str = "test@example.com", password: str = "Secure1!") -> MagicMock:
    """Return a mock User with a real Argon2 password hash."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.name = "Test User"
    user.password_hash = hash_password(password)
    return user


# ── Success path ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.auth.token_repo.create_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_login_success_returns_user_and_tokens(
    mock_get_user, mock_create_token
):
    """Successful login returns a (user, tokens) tuple with access and refresh tokens."""
    user = _make_user()
    mock_get_user.return_value = user
    mock_create_token.return_value = MagicMock()

    db = AsyncMock()
    result_user, tokens = await auth_service.login(db, email=user.email, password="Secure1!")

    assert result_user is user
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert isinstance(tokens["access_token"], str) and len(tokens["access_token"]) > 0
    assert isinstance(tokens["refresh_token"], str) and len(tokens["refresh_token"]) > 0


# ── Failure paths ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_login_unknown_email_raises_invalid_credentials(mock_get_user):
    """Login with an email not in the DB raises InvalidCredentialsError."""
    mock_get_user.return_value = None

    db = AsyncMock()
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, email="nobody@example.com", password="Secure1!")


@pytest.mark.asyncio
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_login_wrong_password_raises_invalid_credentials(mock_get_user):
    """Login with a correct email but wrong password raises InvalidCredentialsError."""
    mock_get_user.return_value = _make_user()

    db = AsyncMock()
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, email="test@example.com", password="WrongPass1!")


@pytest.mark.asyncio
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_login_error_message_is_identical_for_both_failure_cases(mock_get_user):
    """Both unknown-email and wrong-password failures carry the same detail message."""
    db = AsyncMock()

    mock_get_user.return_value = None
    with pytest.raises(InvalidCredentialsError) as exc_unknown:
        await auth_service.login(db, email="nobody@example.com", password="Secure1!")

    mock_get_user.return_value = _make_user()
    with pytest.raises(InvalidCredentialsError) as exc_wrong_pw:
        await auth_service.login(db, email="test@example.com", password="WrongPass1!")

    assert exc_unknown.value.detail == exc_wrong_pw.value.detail


# ── Access token payload ──────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.auth.token_repo.create_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_access_token_payload_contains_sub_exp_iat(
    mock_get_user, mock_create_token
):
    """The access token returned by login contains sub, exp, and iat claims."""
    user = _make_user()
    mock_get_user.return_value = user
    mock_create_token.return_value = MagicMock()

    db = AsyncMock()
    _, tokens = await auth_service.login(db, email=user.email, password="Secure1!")

    payload = jwt.decode(
        tokens["access_token"],
        settings.RSA_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert "sub" in payload
    assert "exp" in payload
    assert "iat" in payload


# ── Refresh token stored as SHA-256 hash ──────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.auth.token_repo.create_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.user_repo.get_user_by_email", new_callable=AsyncMock)
async def test_refresh_token_stored_as_sha256_hash_not_raw(
    mock_get_user, mock_create_token
):
    """create_refresh_token is called with the SHA-256 hash of the raw token,
    never with the raw token itself."""
    user = _make_user()
    mock_get_user.return_value = user
    mock_create_token.return_value = MagicMock()

    db = AsyncMock()
    _, tokens = await auth_service.login(db, email=user.email, password="Secure1!")

    raw_refresh = tokens["refresh_token"]
    expected_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()

    # The hash passed to create_refresh_token must equal SHA-256(raw_token)
    called_with_hash = mock_create_token.call_args.kwargs["token"]
    assert called_with_hash == expected_hash
    assert called_with_hash != raw_refresh  # raw token must never be stored
