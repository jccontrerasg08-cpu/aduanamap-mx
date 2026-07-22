"""Redis cache helper. TTLs are part of the operational contract, not just an
optimization (Banxico explicitly recommends caching to avoid token blocks)."""
from __future__ import annotations

from typing import Optional

try:
    import redis
except Exception:
    redis = None  # type: ignore

from .config import get_settings

_client = None


def client():
    global _client
    if redis is None:
        return None
    if _client is None:
        try:
            _client = redis.from_url(get_settings().redis_url, socket_connect_timeout=2)
        except Exception:
            return None
    return _client


def ping() -> bool:
    c = client()
    if c is None:
        return False
    try:
        return bool(c.ping())
    except Exception:
        return False


def get(key: str) -> Optional[str]:
    c = client()
    if c is None:
        return None
    try:
        v = c.get(key)
        return v.decode() if isinstance(v, bytes) else v
    except Exception:
        return None


def setex(key: str, ttl_seconds: int, value: str) -> None:
    c = client()
    if c is None:
        return
    try:
        c.setex(key, ttl_seconds, value)
    except Exception:
        pass
