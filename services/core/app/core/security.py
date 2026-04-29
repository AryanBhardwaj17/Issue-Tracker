"""
Security utilities for the Core Service.

Core only *verifies* tokens — it never issues them. The RSA private key
stays exclusively in the Auth service; Core holds the public key only.
"""

from jose import JWTError, jwt

from app.core.config import settings


def decode_access_token(token: str) -> dict:
    """Decode and verify an RS256 JWT access token using the RSA public key.

    Args:
        token: A compact JWT string extracted from the Authorization header.

    Returns:
        The decoded payload as a dictionary.
        Expected claims: ``sub`` (user id string), ``name``, ``email``,
        ``iat``, ``exp``, ``type``.

    Raises:
        jose.JWTError: If the token is expired, has an invalid signature,
            or is otherwise malformed. The caller must convert this to a 401.
    """
    return jwt.decode(
        token,
        settings.RSA_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


__all__ = ["decode_access_token", "JWTError"]
