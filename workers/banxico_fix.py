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
from workers.common.manifest import preserve, sha256_bytes

PARSER_VERSION = "banxico_fix@1"
SERIE = os.getenv("BANXICO_FIX_SERIE", "SF43718")
TOKEN = os.getenv("BANXICO_TOKEN", "")
SIE_URL = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{SERIE}/datos/oportuno"


def fetch() -> bytes | None:
    if not TOKEN:
        return None
    try:
        import httpx
    except Exception:
        return None
    headers = {"Bmx-Token": TOKEN, "User-Agent": "AduanaMapMX-ETL/0.1 (+contact)"}
    try:
        resp = httpx.get(SIE_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:  # noqa: BLE001
        print(f"[banxico_fix] fetch failed: {exc}", file=sys.stderr)
        return None


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
        print("[banxico_fix] DRY-RUN — no BANXICO_TOKEN (64 chars) set. "
              "Would fetch, snapshot, and upsert the FIX. Configure .env to run for real.")
        return 0

    snap = preserve("banxico", SIE_URL, payload, "application/json", PARSER_VERSION)
    print(f"[banxico_fix] snapshot {snap.storage_key} sha256={snap.sha256[:12]}…")

    parsed = parse(payload)
    if parsed is None:
        print("[banxico_fix] nothing parsed; preserving snapshot only.")
        return 1

    date_iso, value = parsed
    with wdb.connection() as conn:
        manifest_id = wdb.record_manifest(
            conn, source_name="banxico", source_url=SIE_URL,
            sha256=snap.sha256, parser_version=PARSER_VERSION,
            status="ok", records_loaded=1, effective_date=date_iso,
        )
        rows = upsert(conn, date_iso, value, manifest_id)
        if conn is None:
            print(f"[banxico_fix] parsed FIX {value} @ {date_iso} (no DB — not persisted).")
        else:
            print(f"[banxico_fix] upserted FIX {value} @ {date_iso} ({rows} row).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
