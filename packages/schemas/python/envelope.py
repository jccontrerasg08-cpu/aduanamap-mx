"""Shared API response envelope: every response is data + source_trace + warnings.

This is the single most important contract in the platform. Even an incomplete
answer must be useful and verifiable, so callers always receive:
  - data:         the payload (may be null/partial)
  - source_trace: which official source(s) and snapshot produced the data
  - warnings:     human-readable caveats, e.g. "no confirmable", "stale"
"""
from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceTrace(BaseModel):
    source: str = Field(..., examples=["Banxico", "SNICE", "SRE", "WCO/WITS"])
    label: Optional[str] = Field(None, examples=["SIE_API", "biblioteca_juridica_tlc"])
    fetched_at: Optional[datetime] = None


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    source_trace: list[SourceTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def ok(data: T, *, trace: list[SourceTrace] | None = None,
       warnings: list[str] | None = None) -> Envelope[T]:
    return Envelope[T](data=data, source_trace=trace or [], warnings=warnings or [])


def not_confirmable(reason: str, *, trace: list[SourceTrace] | None = None) -> Envelope[None]:
    """Return when a preference/rate cannot be confirmed from a structured source.

    Product rule: never invent — surface the primary source for human validation.
    """
    return Envelope[None](data=None, source_trace=trace or [], warnings=[f"no confirmable: {reason}"])
