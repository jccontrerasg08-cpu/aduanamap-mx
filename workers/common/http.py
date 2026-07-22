"""Robust HTTP fetch for ETL: identifiable UA, fixed timeout, bounded retry with
exponential backoff + jitter. Returns None on definitive failure so callers fall
back to the previous snapshot instead of crashing the pipeline.
"""
from __future__ import annotations

import random
import time

USER_AGENT = "AduanaMapMX-ETL/0.1 (+https://aduanamap.mx; contacto@aduanamap.mx)"
DEFAULT_TIMEOUT = 15.0
MAX_ATTEMPTS = 3
# Retry only on transient conditions; a 404 won't fix itself on retry.
RETRY_STATUS = {429, 500, 502, 503, 504}


def fetch(url: str, *, headers: dict | None = None, timeout: float = DEFAULT_TIMEOUT,
          max_attempts: int = MAX_ATTEMPTS) -> bytes | None:
    try:
        import httpx
    except Exception:
        return None

    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = httpx.get(url, headers=hdrs, timeout=timeout, follow_redirects=True)
            if resp.status_code in RETRY_STATUS and attempt < max_attempts:
                _sleep_backoff(attempt, retry_after=resp.headers.get("Retry-After"))
                continue
            resp.raise_for_status()
            return resp.content
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < max_attempts:
                _sleep_backoff(attempt)
            continue
    if last_exc is not None:
        print(f"[http] fetch failed after {max_attempts} attempts: {url} -> {last_exc}")
    return None


def _sleep_backoff(attempt: int, *, retry_after: str | None = None) -> None:
    if retry_after:
        try:
            time.sleep(min(float(retry_after), 30.0))
            return
        except (TypeError, ValueError):
            pass
    # Exponential backoff with jitter: ~0.5s, 1s, 2s (+ up to 0.5s jitter).
    time.sleep(min(2 ** (attempt - 1) * 0.5 + random.random() * 0.5, 30.0))
