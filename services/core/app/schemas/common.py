"""
Shared Pydantic schemas used across all Core Service endpoints.

Every API response is wrapped in ``Envelope[T]`` so clients always receive
a consistent shape regardless of the endpoint.
"""

from typing import TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base model that serialises to camelCase JSON and accepts snake_case internally."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Pagination(CamelModel):
    """Pagination metadata returned on every list response."""

    page: int
    page_size: int
    total: int
    total_pages: int


class Envelope[T](CamelModel):
    """Standard response envelope for all API endpoints."""

    success: bool = True
    message: str = "OK"
    data: T | None = None
    pagination: Pagination | None = None


class ErrorDetail(CamelModel):
    """A single field-level validation error."""

    field: str
    message: str


class ErrorEnvelope(CamelModel):
    """Envelope for error responses."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] | None = None


def paginate(page: int, page_size: int, total: int) -> Pagination:
    """Compute pagination metadata from raw counts."""
    total_pages = max(1, -(-total // page_size)) if total > 0 else 0
    return Pagination(page=page, page_size=page_size, total=total, total_pages=total_pages)
