"""
Common response schemas shared across the application.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "ok"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
