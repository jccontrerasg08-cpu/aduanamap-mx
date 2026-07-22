"""Worker-side DB access + manifest/etl_run writers. No-ops cleanly when psycopg
or the database is unavailable so a worker can be smoke-run without infra."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

try:
    import psycopg
except Exception:
    psycopg = None  # type: ignore

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aduana:aduana@localhost:5432/aduanamap")


@contextmanager
def connection() -> Iterator[Optional["psycopg.Connection"]]:
    if psycopg is None:
        yield None
        return
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL, connect_timeout=3)
        yield conn
    except Exception:
        yield None
    finally:
        if conn is not None:
            conn.close()


def record_manifest(conn, *, source_name, source_url, sha256, parser_version,
                    status, records_loaded, effective_date=None) -> Optional[str]:
    if conn is None:
        return None
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO source_manifest
              (source_name, source_url, sha256, parser_version, status,
               records_loaded, effective_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (source_name, source_url, sha256, parser_version, status,
             records_loaded, effective_date),
        )
        manifest_id = cur.fetchone()[0]
    conn.commit()
    return str(manifest_id)
