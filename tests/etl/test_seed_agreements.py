"""Integrity of the curated FTA seed (data/seed/agreements.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from workers import seed_agreements  # noqa: E402

DOC = __import__("json").loads(seed_agreements.SEED.read_text(encoding="utf-8"))
AGREEMENTS = DOC["agreements"]


def test_slugs_unique_and_kebab():
    slugs = [a["slug"] for a in AGREEMENTS]
    assert len(slugs) == len(set(slugs))
    assert all(s == s.lower() and " " not in s for s in slugs)


def test_core_ftas_present():
    slugs = {a["slug"] for a in AGREEMENTS}
    assert {"t-mec", "tlcuem", "tlc-aelc-efta", "cptpp-tipat", "alianza-del-pacifico"} <= slugs


def test_active_agreements_have_dates_and_members():
    for a in AGREEMENTS:
        if a["status"] == "active":
            assert a["effective_date"], f"{a['slug']} sin effective_date"
            assert a["members"], f"{a['slug']} sin miembros"


def test_eu_has_27_members():
    eu = next(a for a in AGREEMENTS if a["slug"] == "tlcuem")
    assert len(eu["members"]) == 27


def test_superseded_point_to_successor():
    for a in AGREEMENTS:
        if a["status"] == "superseded":
            assert a.get("superseded_by"), f"{a['slug']} superado sin superseded_by"
            assert any(x["slug"] == a["superseded_by"] for x in AGREEMENTS)


def test_source_claims_capture_the_disagreement():
    # The report's non-negotiable: SE and ANAM counts differ; both must be stored.
    claims = DOC["source_claims"]
    by_source = {(c["source_name"], c["claim_type"]): c["claim_value"] for c in claims}
    assert by_source[("SE", "tlc_count")] == "14"
    assert by_source[("ANAM", "tlc_count")] == "12"


@pytest.mark.skipif(not seed_agreements.GEOJSON.exists(), reason="geojson no generado")
def test_every_member_iso3_is_a_known_country():
    known = seed_agreements._known_iso3()
    for a in AGREEMENTS:
        for iso3 in a["members"]:
            assert iso3 in known, f"{a['slug']}: ISO3 {iso3} no está en el catálogo de países"
