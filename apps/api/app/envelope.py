"""API-local copy of the shared envelope (see packages/schemas for the canonical
cross-language contract). Kept local so the API package is import-self-contained.

Every API response is `data + source_trace + warnings`. Even a partial or failed
answer is shaped this way so callers can always read what is known, where it came
from, and what could not be confirmed. The platform never fabricates rates,
rules of origin, or preferences — when a value can't be verified from a
structured source it is null/absent and a `no confirmable` warning is emitted.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

NOT_CONFIRMABLE_PREFIX = "no confirmable"


class SourceTrace(BaseModel):
    source: str
    label: Optional[str] = None
    fetched_at: Optional[datetime] = None


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    source_trace: list[SourceTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def ok(
    data: Any,
    *,
    trace: list[dict] | None = None,
    warnings: list[str] | None = None,
) -> dict:
    """Standard success envelope. `trace`/`warnings` default to empty lists."""
    return {"data": data, "source_trace": trace or [], "warnings": warnings or []}


def not_confirmable(reason: str, *, trace: list[dict] | None = None) -> dict:
    """Data could not be confirmed from a structured source — never invent it."""
    return {
        "data": None,
        "source_trace": trace or [],
        "warnings": [f"{NOT_CONFIRMABLE_PREFIX}: {reason}"],
    }


def error(message: str, *, trace: list[dict] | None = None) -> dict:
    """Envelope for an internal failure. Same shape so clients never special-case."""
    return {"data": None, "source_trace": trace or [], "warnings": [message]}
