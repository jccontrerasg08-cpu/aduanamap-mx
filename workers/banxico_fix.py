"""Banxico FIX (SF43718) importer.

Run: python -m workers.banxico_fix

Pipeline: fetch SIE JSON -> preserve raw snapshot (SHA-256) -> record manifest
-> normalize into exchange_rate -> upsert. Banxico recommends caching responses
and enforces rate limits (oportunas: 80/min, 40,000/día). The FIX is published
from 12:00 on bank business days.

Without a BANXICO_TOKEN or DB, the worker runs in dry-run mode and reports what
it *would* do, so the skeleton is exercisable end-to-end.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from workers.common import db as wdb
from workers.common.http import fetch as http_fetch
from workers.common.manifest import preserve

PARSER_VERSION = "banxico_fix@1"
SERIE = os.getenv("BANXICO_FIX_SERIE", "SF43718")
TOKEN = os.getenv("BANXICO_TOKEN", "")
SIE_URL = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{SERIE}/datos/oportuno"


def fetch() -> bytes | None:
    if not TOKEN:
        return None
    # Robust fetch: identifiable UA, timeout, retry/backoff on transient errors.
    return http_fetch(SIE_URL, headers={"Bmx-Token": TOKEN})


def parse(payload: bytes) -> tuple[str, float] | None:
    """Return (date_iso, value) from the SIE 'oportuno' response, or None."""
    try:
        doc = json.loads(payload)
        dato = doc["bmx"]["series"][0]["datos"][0]
        # SIE dates come as dd/mm/YYYY
        d, m, y = dato["fecha"].split("/")
        value = float(str(dato["dato"]).replace(",", ""))
        return f"{y}-{m}-{d}", value
    except Exception as exc:  # noqa: BLE001
        print(f"[banxico_fix] parse failed: {exc}", file=sys.stderr)
        return None


def upsert(conn, date_iso: str, value: float, manifest_id: str | None) -> int:
    if conn is None:
        return 0
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO exchange_rate (series_id, date, value, published_at, source_manifest_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (series_id, date) DO UPDATE
              SET value = EXCLUDED.value, published_at = EXCLUDED.published_at
            """,
            (SERIE, date_iso, value, datetime.now(timezone.utc), manifest_id),
        )
    conn.commit()
    return 1


def run() -> int:
    payload = fetch()

    if payload is None:
        if not TOKEN:
            print("[banxico_fix] DRY-RUN — no BANXICO_TOKEN (64 chars) set. "
                  "Would fetch, snapshot, and upsert the FIX. Configure .env to run for real.")
            return 0
        # Token present but fetch failed after retries → record the failed run so
        # /api/sources/status shows the source as unhealthy, then fall back.
        with wdb.connection() as conn:
            run_id = wdb.start_run(conn, "banxico")
            wdb.log_error(conn, run_id, severity="error", stage="fetch",
                          message="SIE fetch failed after retries", error_json={"url": SIE_URL})
            wdb.finish_run(conn, run_id, status="error")
        print("[banxico_fix] fetch failed after retries; previous snapshot remains authoritative.")
        return 1

    snap = preserve("banxico", SIE_URL, payload, "application/json", PARSER_VERSION)
    print(f"[banxico_fix] snapshot {snap.storage_key} sha256={snap.sha256[:12]}…")

    with wdb.connection() as conn:
        run_id = wdb.start_run(conn, "banxico")
        parsed = parse(payload)
        if parsed is None:
            wdb.record_manifest(
                conn, source_name="banxico", source_url=SIE_URL, sha256=snap.sha256,
                parser_version=PARSER_VERSION, status="error", records_loaded=0,
            )
            wdb.log_error(conn, run_id, severity="error", stage="parse",
                          message="unexpected SIE payload shape")
            wdb.finish_run(conn, run_id, status="error", rows_read=1)
            print("[banxico_fix] nothing parsed; preserving snapshot only.")
            return 1

        date_iso, value = parsed
        manifest_id = wdb.record_manifest(
            conn, source_name="banxico", source_url=SIE_URL, sha256=snap.sha256,
            parser_version=PARSER_VERSION, status="ok", records_loaded=1, effective_date=date_iso,
        )
        rows = upsert(conn, date_iso, value, manifest_id)
        wdb.finish_run(conn, run_id, status="ok", rows_read=1, rows_loaded=rows)
        if conn is None:
            print(f"[banxico_fix] parsed FIX {value} @ {date_iso} (no DB — not persisted).")
        else:
            print(f"[banxico_fix] upserted FIX {value} @ {date_iso} ({rows} row).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
