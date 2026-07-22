"""Thin Postgres access helpers. Uses psycopg3. Degrades gracefully: callers
treat a None connection as "dependency down" rather than crashing the request."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

try:
    import psycopg
except Exception:  # psycopg optional at import time (e.g. docs build)
    psycopg = None  # type: ignore

from .config import get_settings


@contextmanager
def connection() -> Iterator[Optional["psycopg.Connection"]]:
    if psycopg is None:
        yield None
        return
    conn = None
    try:
        conn = psycopg.connect(get_settings().database_url, connect_timeout=3)
        yield conn
    except Exception:
        yield None
    finally:
        if conn is not None:
            conn.close()


def ping() -> bool:
    with connection() as conn:
        if conn is None:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except Exception:
            return False
