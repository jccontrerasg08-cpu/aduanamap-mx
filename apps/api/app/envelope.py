"""API-local copy of the shared envelope (see packages/schemas for the canonical
cross-language contract). Kept local so the API package is import-self-contained."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceTrace(BaseModel):
    source: str
    label: Optional[str] = None
    fetched_at: Optional[datetime] = None


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    source_trace: list[SourceTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def ok(data, *, trace=None, warnings=None):
    return {"data": data, "source_trace": trace or [], "warnings": warnings or []}
