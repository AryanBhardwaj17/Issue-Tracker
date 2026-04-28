"""
SQLAlchemy async engine and declarative Base for the Core Service.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Shared declarative base for all Core Service ORM models."""
