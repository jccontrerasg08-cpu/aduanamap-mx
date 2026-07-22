"""Liveness + dependency health. TTL 30s (see report cache table)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from .. import cache, db
from ..config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/api/healthz")
def healthz():
    settings = get_settings()
    deps = {
        "postgres": "ok" if db.ping() else "down",
        "redis": "ok" if cache.ping() else "down",
    }
    overall = "ok" if all(v == "ok" for v in deps.values()) else "degraded"
    return {
        "status": overall,
        "version": settings.version,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "dependencies": deps,
    }
