"""
Security utilities for the auth service.

Responsibilities:
- Password hashing and verification via Argon2 (memory-hard, resistant to brute-force).
- JWT access token creation and decoding using RS256 (asymmetric — private key signs,
  public key verifies; the public key can be shared safely with other services).
- Opaque refresh token generation and SHA-256 hashing (the raw token is given to the
  client; only its hash is stored in the database).

All key material is read exclusively from ``app.core.config.settings`` — never
from the environment directly.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt

from app.core.config import settings

# ── Argon2 hasher (singleton) ─────────────────────────────────────────────────
# Default parameters (time_cost=3, memory_cost=65536, parallelism=4) are
# deliberately left at library defaults — they balance security and latency.
_ph = PasswordHasher()


# ── Password utilities ────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return an Argon2id hash of ``plain``.

    The resulting string includes the algorithm parameters and salt, so it is
    self-contained and safe to store directly in the database.
    """
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if ``plain`` matches the stored Argon2 ``hashed`` value.

    Returns False (rather than raising) on any mismatch or invalid hash so
    callers can treat the result as a simple boolean check.
    """
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        # Catches invalid hash format, etc. — treat as failed verification.
        return False


# ── JWT utilities ─────────────────────────────────────────────────────────────


def create_access_token(
    subject: str,
    extra_claims: dict | None = None,
) -> str:
    """Create a signed RS256 JWT access token.

    Args:
        subject: The ``sub`` claim — typically the user's integer id as a string.
        extra_claims: Optional additional claims merged into the payload
            (e.g. ``{"username": "alice"}``).  Do NOT include ``exp`` here;
            it is computed automatically from ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        A compact, URL-safe JWT string.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.RSA_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and verify an RS256 JWT access token.

    Uses the RSA public key so this function is safe to call from any service
    that has access to the public key only.

    Args:
        token: A compact JWT string.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        jose.JWTError: If the token is expired, has an invalid signature,
            or is otherwise malformed.
    """
    return jwt.decode(
        token,
        settings.RSA_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Refresh token utilities ───────────────────────────────────────────────────


def generate_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token.

    Returns a 32-byte URL-safe hex string (64 characters).  This raw value is
    sent to the client; only its SHA-256 hash is stored in the database.
    """
    return secrets.token_hex(32)


def hash_refresh_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of ``raw_token``.

    Stored in the ``refresh_tokens.token`` column (always 64 chars).
    Hashing ensures that a database leak does not expose usable tokens.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()
