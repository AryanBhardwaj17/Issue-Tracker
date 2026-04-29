"""
Unit tests for access token and refresh token logic in app.core.security.

These tests are purely in-memory — no DB, no HTTP.  They validate:

  - create_access_token produces a decodable RS256 JWT.
  - The decoded payload contains the required claims: sub, exp, iat.
  - The token type claim is "access".
  - Token expiry is approximately ACCESS_TOKEN_EXPIRE_MINUTES from now.
  - generate_refresh_token returns a 64-character hex string.
  - hash_refresh_token returns the correct SHA-256 hex digest.
  - Two calls to generate_refresh_token produce different tokens (uniqueness).
  - Hashing the same raw token twice produces the same digest (determinism).
  - Different raw tokens produce different hashes (collision avoidance).
"""

import hashlib
import time
import uuid

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


# ── Access token ──────────────────────────────────────────────────────────────


def test_access_token_is_decodable():
    """create_access_token produces a JWT that can be decoded with the public key."""
    subject = str(uuid.uuid4())
    token = create_access_token(subject=subject)

    payload = decode_access_token(token)
    assert payload["sub"] == subject


def test_access_token_contains_sub_exp_iat():
    """Decoded payload contains sub, exp, and iat claims."""
    subject = str(uuid.uuid4())
    token = create_access_token(subject=subject)
    payload = decode_access_token(token)

    assert "sub" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_type_claim_is_access():
    """The token carries a 'type' claim set to 'access'."""
    token = create_access_token(subject=str(uuid.uuid4()))
    payload = decode_access_token(token)

    assert payload.get("type") == "access"


def test_access_token_expiry_is_within_expected_window():
    """Token expiry is roughly ACCESS_TOKEN_EXPIRE_MINUTES minutes in the future."""
    before = time.time()
    token = create_access_token(subject=str(uuid.uuid4()))
    after = time.time()

    payload = decode_access_token(token)
    exp = payload["exp"]
    expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Allow ±5 seconds for test execution time
    assert before + expected_seconds - 5 <= exp <= after + expected_seconds + 5


def test_access_token_algorithm_is_rs256():
    """The JWT header declares RS256 as the algorithm."""
    token = create_access_token(subject=str(uuid.uuid4()))
    # Decode without verification to inspect the header
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"


def test_access_token_subject_is_preserved():
    """The sub claim exactly matches the subject passed to create_access_token."""
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id


def test_access_token_extra_claims_are_included():
    """Extra claims passed via extra_claims appear in the decoded payload."""
    extra = {"name": "Alice", "email": "alice@example.com"}
    token = create_access_token(subject=str(uuid.uuid4()), extra_claims=extra)
    payload = decode_access_token(token)

    assert payload["name"] == "Alice"
    assert payload["email"] == "alice@example.com"


# ── Refresh token ─────────────────────────────────────────────────────────────


def test_generate_refresh_token_returns_64_char_hex():
    """generate_refresh_token returns a 64-character lowercase hex string."""
    token = generate_refresh_token()
    assert len(token) == 64
    # Must be valid hex
    int(token, 16)


def test_generate_refresh_token_is_unique():
    """Two consecutive calls produce different tokens."""
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2


def test_hash_refresh_token_returns_sha256_digest():
    """hash_refresh_token returns the correct SHA-256 hex digest."""
    raw = generate_refresh_token()
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert hash_refresh_token(raw) == expected


def test_hash_refresh_token_is_deterministic():
    """Hashing the same raw token twice returns the same digest."""
    raw = generate_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)


def test_hash_refresh_token_different_inputs_produce_different_hashes():
    """Two different raw tokens produce two different hashes."""
    raw1 = generate_refresh_token()
    raw2 = generate_refresh_token()
    assert hash_refresh_token(raw1) != hash_refresh_token(raw2)


def test_hash_refresh_token_digest_is_64_chars():
    """SHA-256 hex digest is always 64 characters."""
    raw = generate_refresh_token()
    digest = hash_refresh_token(raw)
    assert len(digest) == 64
