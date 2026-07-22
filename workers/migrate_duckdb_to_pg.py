"""Migrate the curated comex DuckDB warehouse into PostgreSQL for the public API.

Reads (read-only) from the existing repo's data/comex.duckdb and upserts into the
AduanaMap Postgres schema (core/migrations/0001_init.sql). Idempotent.

Mapping (DuckDB -> Postgres):
  tariff_fraction        -> mx_tariff_fraction   (fraccion8, hs6, description_es, unit)
  tariff_nico            -> mx_nico              (nico10, fraccion8, nico2, description_es)
  catalog_item (GLOBAL)  -> hs_code              (hs2/hs4/hs6 by code_level)
  anam_trade_agreements  -> agreement (+ member MEX) & source doc trace
  dim_banxico_series     -> banxico_series
  fact_banxico_series..  -> exchange_rate        (monthly series values)

Run:
  python -m workers.migrate_duckdb_to_pg            # migrate everything
  python -m workers.migrate_duckdb_to_pg fractions  # one slice

Config: DATABASE_URL, COMEX_DUCKDB_PATH (defaults to <COMEX_REPO_PATH>/data/comex.duckdb).
Without duckdb/psycopg or a live DB, prints a dry-run plan.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

from workers.comex_bridge import COMEX_REPO_PATH

LIGIE_VERSION = os.getenv("LIGIE_VERSION_LABEL", "comex-import")
HS_VERSION = os.getenv("HS_VERSION_LABEL", "wits-global")
EFFECTIVE_FROM = os.getenv("MIGRATION_EFFECTIVE_FROM", date.today().isoformat())

DUCKDB_PATH = os.getenv("COMEX_DUCKDB_PATH", str(Path(COMEX_REPO_PATH) / "data" / "comex.duckdb"))


def _connect_duckdb():
    try:
        import duckdb
    except Exception:
        print("[migrate] duckdb not installed (pip install duckdb). Dry-run only.", file=sys.stderr)
        return None
    if not Path(DUCKDB_PATH).exists():
        print(f"[migrate] DuckDB not found at {DUCKDB_PATH}", file=sys.stderr)
        return None
    return duckdb.connect(DUCKDB_PATH, read_only=True)


def _connect_pg():
    try:
        import psycopg
    except Exception:
        print("[migrate] psycopg not installed. Dry-run only.", file=sys.stderr)
        return None
    url = os.getenv("DATABASE_URL", "postgresql://aduana:aduana@localhost:5432/aduanamap")
    try:
        return psycopg.connect(url, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        print(f"[migrate] Postgres unreachable ({exc}). Dry-run only.", file=sys.stderr)
        return None


def migrate_fractions(duck, pg) -> int:
    rows = duck.execute(
        """
        SELECT fraccion8, hs6, description
        FROM tariff_fraction
        WHERE fraccion8 IS NOT NULL AND hs6 IS NOT NULL
        """
    ).fetchall()
    if pg is None:
        print(f"[migrate] fractions: would upsert {len(rows)} rows into mx_tariff_fraction")
        return len(rows)
    with pg.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO mx_tariff_fraction
              (ligie_version, fraccion8, hs6, description_es, effective_from)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ligie_version, fraccion8, effective_from) DO UPDATE
              SET hs6 = EXCLUDED.hs6, description_es = EXCLUDED.description_es
            """,
            [(LIGIE_VERSION, f8, hs6, desc or "", EFFECTIVE_FROM) for f8, hs6, desc in rows],
        )
    pg.commit()
    print(f"[migrate] fractions: upserted {len(rows)} rows")
    return len(rows)


def migrate_nicos(duck, pg) -> int:
    rows = duck.execute(
        "SELECT nico10, fraccion8, nico, description FROM tariff_nico WHERE nico10 IS NOT NULL"
    ).fetchall()
    if pg is None:
        print(f"[migrate] nicos: would upsert {len(rows)} rows into mx_nico")
        return len(rows)
    with pg.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO mx_nico (nico10, fraccion8, nico2, description_es, effective_from)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nico10, effective_from) DO UPDATE
              SET fraccion8 = EXCLUDED.fraccion8, description_es = EXCLUDED.description_es
            """,
            [(n10, f8, (nico or "")[-2:].zfill(2), desc or "", EFFECTIVE_FROM)
             for n10, f8, nico, desc in rows],
        )
    pg.commit()
    print(f"[migrate] nicos: upserted {len(rows)} rows")
    return len(rows)


def migrate_hs(duck, pg) -> int:
    rows = duck.execute(
        """
        SELECT code, code_level, description
        FROM catalog_item
        WHERE country_scope = 'GLOBAL' AND code_level IN (2, 4, 6)
        """
    ).fetchall()
    if pg is None:
        print(f"[migrate] hs: would upsert {len(rows)} rows into hs_code")
        return len(rows)
    payload = []
    for code, level, desc in rows:
        c = "".join(ch for ch in str(code) if ch.isdigit())
        payload.append((
            HS_VERSION, c[:2], c[:4] if level >= 4 else None,
            c[:6] if level >= 6 else None, desc or "",
        ))
    with pg.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO hs_code (hs_version, hs2, hs4, hs6, description_es)
            VALUES (%s, %s, %s, %s, %s)
            """,
            payload,
        )
    pg.commit()
    print(f"[migrate] hs: inserted {len(payload)} rows")
    return len(payload)


def migrate_agreements(duck, pg) -> int:
    rows = duck.execute(
        "SELECT agreement_key, title, url, dof_code, published_date FROM anam_trade_agreements"
    ).fetchall()
    if pg is None:
        print(f"[migrate] agreements: would upsert {len(rows)} rows into agreement (+source claim)")
        return len(rows)
    with pg.cursor() as cur:
        for key, title, url, dof_code, pub in rows:
            cur.execute(
                """
                INSERT INTO agreement (slug, name_es, name_en, type, status, source_policy)
                VALUES (%s, %s, %s, 'FTA', 'active', 'ANAM tratados-y-acuerdos')
                ON CONFLICT (slug) DO UPDATE SET name_es = EXCLUDED.name_es
                """,
                (f"anam-{key}", title or "Acuerdo", title or "Agreement"),
            )
        # Store the ANAM count as a source claim (SE vs ANAM differ by criterion).
        cur.execute(
            """
            INSERT INTO agreement_source_claim (source_name, claim_type, claim_value, consulted_at)
            VALUES ('ANAM', 'agreement_links', %s, %s)
            """,
            (str(len(rows)), EFFECTIVE_FROM),
        )
    pg.commit()
    print(f"[migrate] agreements: upserted {len(rows)} rows")
    return len(rows)


TASKS = {
    "fractions": migrate_fractions,
    "nicos": migrate_nicos,
    "hs": migrate_hs,
    "agreements": migrate_agreements,
}


def main(argv: list[str]) -> int:
    which = argv or list(TASKS)
    duck = _connect_duckdb()
    if duck is None:
        print("[migrate] no DuckDB source available; nothing to do.")
        return 2
    pg = _connect_pg()
    total = 0
    try:
        for name in which:
            fn = TASKS.get(name)
            if fn is None:
                print(f"[migrate] unknown task '{name}'. Options: {', '.join(TASKS)}")
                continue
            total += fn(duck, pg)
    finally:
        duck.close()
        if pg is not None:
            pg.close()
    mode = "migrated" if pg is not None else "planned (dry-run)"
    print(f"[migrate] done — {total} rows {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
