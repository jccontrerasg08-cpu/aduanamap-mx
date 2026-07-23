"""Seed Mexico's Free Trade Agreements into `agreement` / `agreement_member` /
`agreement_source_claim` from the curated `data/seed/agreements.json`.

The JSON is the canonical, in-repo catalogue of Mexico's TLCs (researched from SE,
SICE-OEA and Wikipedia). Members are ISO-3166 alpha-3 partner countries, so they
link straight to the `country` table and drive the map's per-country coloring.

The `agreement_source_claim` rows record the deliberate "conteo según fuente"
tension the report flags (SE 14/52 vs ANAM 12/46 vs Wikipedia 13/46) — stored as
claims, not resolved into one "true" number.

Validation (runs even in DRY-RUN, no DB needed): every member ISO3 must exist in
the built countries GeoJSON; an unknown code is almost always a typo and fails.

Run: python -m workers.seed_agreements     (depends on seed_countries for members)
"""
from __future__ import annotations

import json
from pathlib import Path

from workers.common import db as wdb

PARSER_VERSION = "seed_agreements@1"
ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed" / "agreements.json"
GEOJSON = ROOT / "apps" / "web" / "public" / "geo" / "countries-50m.geojson"

_UPSERT_AGREEMENT = """
INSERT INTO agreement (slug, name_es, name_en, type, status, signed_date, effective_date, source_policy)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (slug) DO UPDATE
  SET name_es = EXCLUDED.name_es, name_en = EXCLUDED.name_en, type = EXCLUDED.type,
      status = EXCLUDED.status, signed_date = EXCLUDED.signed_date,
      effective_date = EXCLUDED.effective_date, source_policy = EXCLUDED.source_policy
RETURNING id
"""

_UPSERT_MEMBER = """
INSERT INTO agreement_member (agreement_id, country_id, role, valid_from)
SELECT %s, c.id, 'partner', %s FROM country c WHERE c.iso3 = %s
ON CONFLICT (agreement_id, country_id) DO NOTHING
"""

_INSERT_CLAIM = """
INSERT INTO agreement_source_claim (source_name, claim_type, claim_value, consulted_at, notes)
VALUES (%s, %s, %s, %s, %s)
"""


def _known_iso3() -> set[str]:
    if not GEOJSON.exists():
        return set()
    fc = json.loads(GEOJSON.read_text(encoding="utf-8"))
    return {f["properties"]["iso3"] for f in fc["features"] if f["properties"].get("iso3")}


def _validate(doc: dict) -> list[str]:
    """Return a list of problems (unknown member ISO3s). Empty = all good."""
    known = _known_iso3()
    problems: list[str] = []
    if not known:
        problems.append("catálogo de países no generado; no se pudo validar ISO3 de miembros")
        return problems
    for a in doc["agreements"]:
        for iso3 in a["members"]:
            if iso3 not in known:
                problems.append(f"{a['slug']}: ISO3 desconocido '{iso3}'")
    return problems


def run() -> int:
    if not SEED.exists():
        print(f"[seed_agreements] falta {SEED}")
        return 1
    doc = json.loads(SEED.read_text(encoding="utf-8"))
    agreements = doc["agreements"]
    claims = doc.get("source_claims", [])
    member_links = sum(len(a["members"]) for a in agreements)

    problems = _validate(doc)
    for p in problems:
        print(f"[seed_agreements] VALIDACIÓN: {p}")
    # Unknown ISO3 is a data error (typo) — never load silently.
    if any("ISO3 desconocido" in p for p in problems):
        return 1

    active = sum(1 for a in agreements if a["status"] == "active")
    print(f"[seed_agreements] {len(agreements)} instrumentos ({active} vigentes, "
          f"{len(agreements) - active} superados), {member_links} membresías, {len(claims)} claims por fuente")

    with wdb.connection() as conn:
        run_id = wdb.start_run(conn, "seed_agreements")
        if conn is None:
            print("[seed_agreements] DRY-RUN — sin base de datos. Validación OK; no persistido.")
            return 0
        loaded_m = 0
        try:
            with conn.cursor() as cur:
                for a in agreements:
                    cur.execute(_UPSERT_AGREEMENT, (
                        a["slug"], a["name_es"], a["name_en"], a["type"], a["status"],
                        a.get("signed_date"), a.get("effective_date"), a.get("source_policy"),
                    ))
                    agreement_id = cur.fetchone()[0]
                    for iso3 in a["members"]:
                        cur.execute(_UPSERT_MEMBER, (agreement_id, a.get("effective_date"), iso3))
                        loaded_m += cur.rowcount or 0
                for c in claims:
                    cur.execute(_INSERT_CLAIM, (
                        c["source_name"], c["claim_type"], c["claim_value"],
                        c["consulted_at"], c.get("notes"),
                    ))
            conn.commit()
            wdb.record_manifest(conn, source_name="seed_agreements", source_url=str(SEED),
                                sha256="", parser_version=PARSER_VERSION, status="ok",
                                records_loaded=len(agreements))
            wdb.finish_run(conn, run_id, status="ok", rows_read=len(agreements), rows_loaded=len(agreements))
            print(f"[seed_agreements] upsert de {len(agreements)} tratados, {loaded_m} membresías, "
                  f"{len(claims)} claims OK.")
        except Exception as exc:  # noqa: BLE001
            wdb.log_error(conn, run_id, severity="error", stage="upsert", message=str(exc))
            wdb.finish_run(conn, run_id, status="error")
            print(f"[seed_agreements] error: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
