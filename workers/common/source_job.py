"""Shared capture stage for source importers.

The report's pipeline is capture → preserve → parse → normalize → publish.
The first two stages are identical across sources and are the ones that protect
legal traceability, so they live here. Each importer supplies its own parser for
the later stages; until it does, `capture_only` still runs the valuable part:
fetch the raw artifact, hash + store it, and record a manifest + etl_run.
"""
from __future__ import annotations

import os

from . import db as wdb
from .http import fetch
from .manifest import preserve


def capture_only(source_name: str, url_env: str, *, parser_version: str,
                 content_type: str = "application/octet-stream") -> int:
    """Fetch + preserve + record for a source whose parser isn't built yet.

    URL comes from an env var so no endpoint is hard-coded before it's verified.
    Returns a process exit code (0 ok / dry-run, 1 failure).
    """
    url = os.getenv(url_env, "")
    if not url:
        print(f"[{source_name}] DRY-RUN — set {url_env} to enable capture. "
              f"Parser ({parser_version}) pending: normalize stage TODO.")
        return 0

    payload = fetch(url)
    with wdb.connection() as conn:
        run_id = wdb.start_run(conn, source_name)
        if payload is None:
            wdb.log_error(conn, run_id, severity="error", stage="capture",
                          message="fetch failed after retries", error_json={"url": url})
            wdb.finish_run(conn, run_id, status="error")
            print(f"[{source_name}] capture failed; previous snapshot remains authoritative.")
            return 1

        snap = preserve(source_name, url, payload, content_type, parser_version)
        wdb.record_manifest(
            conn, source_name=source_name, source_url=url, sha256=snap.sha256,
            parser_version=parser_version, status="captured", records_loaded=0,
        )
        wdb.finish_run(conn, run_id, status="ok", rows_read=1, rows_loaded=0)
        print(f"[{source_name}] captured snapshot {snap.storage_key} "
              f"sha256={snap.sha256[:12]}… (parse/normalize pending).")
    return 0
