"""Per-client rate limiting → HTTP 429 + Retry-After.

Fixed-window counter keyed by (client, route-bucket). Uses Redis (INCR + EXPIRE)
so limits hold across API replicas; falls back to an in-process counter when
Redis is down so a cache outage never removes the protection entirely.

Limits mirror the report's public API table (per-minute, anonymous).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from . import cache

DEFAULT_LIMIT = 60  # requests per window
WINDOW_SECONDS = 60

# Route prefix → requests per WINDOW_SECONDS (report §API pública).
ROUTE_LIMITS: dict[str, int] = {
    # Free-text AI surface: tightest bucket, it is the most abuse-prone endpoint.
    "/api/assistant": 10,
    "/api/classify": 10,
    "/api/calculator": 10,
    "/api/banxico": 20,
    "/api/sources": 20,
    "/api/tariff": 30,
}


def limit_for(path: str) -> int:
    for prefix, value in ROUTE_LIMITS.items():
        if path.startswith(prefix):
            return value
    return DEFAULT_LIMIT


@dataclass
class Decision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


# In-process fallback: {key: (count, window_start_epoch)}
_local: dict[str, tuple[int, float]] = {}


def _bucket(now: float) -> int:
    return int(now // WINDOW_SECONDS)


def check(client_id: str, path: str, *, now: float | None = None) -> Decision:
    now = now if now is not None else time.time()
    limit = limit_for(path)
    window = _bucket(now)
    key = f"rl:{client_id}:{path}:{window}"
    reset_in = WINDOW_SECONDS - int(now % WINDOW_SECONDS)

    count = _incr_redis(key)
    if count is None:  # Redis unavailable → local fallback.
        count = _incr_local(key, now)

    remaining = max(0, limit - count)
    allowed = count <= limit
    return Decision(allowed=allowed, limit=limit, remaining=remaining,
                    retry_after=reset_in if not allowed else 0)


def _incr_redis(key: str) -> int | None:
    c = cache.client()
    if c is None:
        return None
    try:
        pipe = c.pipeline()
        pipe.incr(key)
        pipe.expire(key, WINDOW_SECONDS)
        count, _ = pipe.execute()
        return int(count)
    except Exception:
        return None


def _incr_local(key: str, now: float) -> int:
    count, start = _local.get(key, (0, now))
    if now - start >= WINDOW_SECONDS:
        count, start = 0, now
    count += 1
    _local[key] = (count, start)
    # Opportunistic cleanup so the dict cannot grow unbounded.
    if len(_local) > 10_000:
        cutoff = now - WINDOW_SECONDS
        for k, (_, s) in list(_local.items()):
            if s < cutoff:
                _local.pop(k, None)
    return count
