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


def start_run(conn, source_name: str) -> Optional[str]:
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_run (source_name, status) VALUES (%s, 'running') RETURNING id",
                (source_name,),
            )
            run_id = cur.fetchone()[0]
        conn.commit()
        return str(run_id)
    except Exception:
        return None


def finish_run(conn, run_id: Optional[str], *, status: str,
               rows_read: int = 0, rows_loaded: int = 0) -> None:
    if conn is None or run_id is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE etl_run
                   SET status = %s, finished_at = now(), rows_read = %s, rows_loaded = %s
                 WHERE id = %s
                """,
                (status, rows_read, rows_loaded, run_id),
            )
        conn.commit()
    except Exception:
        pass


def log_error(conn, run_id: Optional[str], *, severity: str, stage: str,
              message: str, error_json: Optional[dict] = None) -> None:
    """Persist an ETL error. Best-effort: never raises out of the pipeline."""
    if conn is None or run_id is None:
        return
    try:
        import json
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO etl_error_log (etl_run_id, severity, stage, message, error_json)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (run_id, severity, stage, message,
                 json.dumps(error_json) if error_json is not None else None),
            )
        conn.commit()
    except Exception:
        pass
