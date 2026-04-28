"""
ORM model registry.

Importing this package ensures all model classes are registered with
``Base.metadata``.  Alembic's env.py imports this module so that
``--autogenerate`` can detect all tables.
"""

from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["RefreshToken", "User"]
