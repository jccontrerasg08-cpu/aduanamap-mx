"""Shared ETL primitives used by every worker.

- `http`       — robust fetch: identifiable UA, timeout, retry + exponential backoff
- `manifest`   — SHA-256 raw-snapshot preservation (capture/preserve stages)
- `db`         — Postgres access + source_manifest / etl_run / etl_error_log writers
- `source_job` — shared capture-only stage for sources whose parser isn't built yet

All degrade cleanly (no-op / return None) when psycopg, httpx, or the database
is unavailable, so a worker never crashes the pipeline on a dependency outage.
"""
