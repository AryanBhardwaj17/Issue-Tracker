"""Security utilities — token verification only (no signing)."""

from jose import JWTError, jwt

from app.core.config import settings


def decode_access_token(token: str) -> dict:
    """Decode and verify an RS256 JWT access token using the RSA public key.

    Returns the decoded payload dict.
    Raises ``jose.JWTError`` if the token is invalid — the caller maps this to 401.
    """
    return jwt.decode(
        token,
        settings.RSA_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


__all__ = ["decode_access_token", "JWTError"]
