"""Seed the `country` table from the built world-map GeoJSON.

Single source of truth: `apps/web/public/geo/countries-50m.geojson` (produced by
`tools/map-build/build-countries.mjs`) already carries, per feature, the country
attributes we need — iso3, iso2, name_es, name_en, region, subregion — joined by
numeric ISO (ccn3), which is why France/Norway/Kosovo are present (see ADR 0004).
Reusing it avoids a second country data source drifting out of sync.

Pipeline: read GeoJSON → upsert `country` → record etl_run. Neutral features
(iso3 = null: Kosovo, Somaliland, N. Cyprus…) are skipped and counted. Runs in
DRY-RUN without a database.

Run: python -m workers.seed_countries
"""
from __future__ import annotations

import json
from pathlib import Path

from workers.common import db as wdb

PARSER_VERSION = "seed_countries@1"
GEOJSON = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "geo" / "countries-50m.geojson"

_UPSERT = """
INSERT INTO country (iso2, iso3, name_es, name_en, region, subregion, active)
VALUES (%s, %s, %s, %s, %s, %s, TRUE)
ON CONFLICT (iso3) DO UPDATE
  SET iso2 = EXCLUDED.iso2, name_es = EXCLUDED.name_es, name_en = EXCLUDED.name_en,
      region = EXCLUDED.region, subregion = EXCLUDED.subregion, updated_at = now()
"""


def _rows() -> list[tuple]:
    """Extract (iso2, iso3, name_es, name_en, region, subregion) for real countries."""
    fc = json.loads(GEOJSON.read_text(encoding="utf-8"))
    rows, skipped = [], 0
    for f in fc.get("features", []):
        p = f.get("properties", {})
        iso3 = p.get("iso3")
        if not iso3:  # neutral feature (no UN code) — not a catalog country
            skipped += 1
            continue
        rows.append((p.get("iso2"), iso3, p.get("name_es"), p.get("name_en"),
                     p.get("region"), p.get("subregion")))
    print(f"[seed_countries] {len(rows)} países; {skipped} features neutrales omitidas")
    return rows


def run() -> int:
    if not GEOJSON.exists():
        print(f"[seed_countries] falta {GEOJSON}. Genera con: "
              f"cd tools/map-build && npm install && node build-countries.mjs")
        return 1

    rows = _rows()
    with wdb.connection() as conn:
        run_id = wdb.start_run(conn, "seed_countries")
        if conn is None:
            print(f"[seed_countries] DRY-RUN — sin base de datos. Cargaría {len(rows)} países.")
            return 0
        try:
            with conn.cursor() as cur:
                cur.executemany(_UPSERT, rows)
            conn.commit()
            wdb.record_manifest(conn, source_name="seed_countries", source_url=str(GEOJSON),
                                sha256="", parser_version=PARSER_VERSION, status="ok",
                                records_loaded=len(rows))
            wdb.finish_run(conn, run_id, status="ok", rows_read=len(rows), rows_loaded=len(rows))
            print(f"[seed_countries] upsert de {len(rows)} países OK.")
        except Exception as exc:  # noqa: BLE001
            wdb.log_error(conn, run_id, severity="error", stage="upsert", message=str(exc))
            wdb.finish_run(conn, run_id, status="error")
            print(f"[seed_countries] error: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
