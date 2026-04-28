"""
SQLAlchemy async engine and declarative Base for the Notification Service.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Shared declarative base for all Notification Service ORM models."""
