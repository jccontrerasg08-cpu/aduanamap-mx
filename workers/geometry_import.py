"""Import country polygons into PostGIS (`country_geometry`).

Optional for the current map (the web renders the static GeoJSON directly), but
populates `country_geometry` for future server-side spatial queries (e.g. "países
de una región", vecindad). Same single source as the map + seeder:
`apps/web/public/geo/countries-50m.geojson`.

Pipeline: read GeoJSON → for each feature with an iso3, resolve country_id and
upsert its geometry (coerced to MultiPolygon, SRID 4326) with source hash for
traceability. Neutral features (iso3 = null) are skipped. Depends on
`seed_countries` having populated `country`. DRY-RUN without a database.

Run: python -m workers.geometry_import
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from workers.common import db as wdb

PARSER_VERSION = "geometry_import@1"
SOURCE_NAME = "world-atlas-50m"
GEOJSON = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "geo" / "countries-50m.geojson"

_UPSERT = """
INSERT INTO country_geometry (country_id, geom, source_name, source_hash)
SELECT c.id,
       ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
       %s, %s
FROM country c
WHERE c.iso3 = %s
ON CONFLICT (country_id) DO UPDATE
  SET geom = EXCLUDED.geom, source_name = EXCLUDED.source_name,
      source_hash = EXCLUDED.source_hash, created_at = now()
"""


def run() -> int:
    if not GEOJSON.exists():
        print(f"[geometry_import] falta {GEOJSON}. Genera con build-countries.mjs primero.")
        return 1

    fc = json.loads(GEOJSON.read_text(encoding="utf-8"))
    feats = [f for f in fc.get("features", []) if f.get("properties", {}).get("iso3")]
    skipped = len(fc.get("features", [])) - len(feats)

    with wdb.connection() as conn:
        run_id = wdb.start_run(conn, "geometry_import")
        if conn is None:
            print(f"[geometry_import] DRY-RUN — sin DB. Cargaría {len(feats)} geometrías "
                  f"({skipped} neutrales omitidas).")
            return 0
        loaded = 0
        try:
            with conn.cursor() as cur:
                for f in feats:
                    iso3 = f["properties"]["iso3"]
                    geom_json = json.dumps(f["geometry"])
                    src_hash = hashlib.sha256(geom_json.encode()).hexdigest()
                    cur.execute(_UPSERT, (geom_json, SOURCE_NAME, src_hash, iso3))
                    loaded += cur.rowcount or 0
            conn.commit()
            wdb.record_manifest(conn, source_name=SOURCE_NAME, source_url=str(GEOJSON),
                                sha256="", parser_version=PARSER_VERSION, status="ok",
                                records_loaded=loaded)
            wdb.finish_run(conn, run_id, status="ok", rows_read=len(feats), rows_loaded=loaded)
            print(f"[geometry_import] {loaded} geometrías cargadas "
                  f"({len(feats) - loaded} sin país correspondiente — ejecuta seed_countries).")
        except Exception as exc:  # noqa: BLE001
            wdb.log_error(conn, run_id, severity="error", stage="upsert", message=str(exc))
            wdb.finish_run(conn, run_id, status="error")
            print(f"[geometry_import] error: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
