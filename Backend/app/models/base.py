"""
Base model with common fields for MongoDB documents.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin that adds created_at / updated_at timestamps."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
