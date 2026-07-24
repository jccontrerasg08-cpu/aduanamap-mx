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


def test_partial_scope_is_never_labeled_as_fta():
    """An ACE/AAP must be clearly marked: conflating it with a TLC misleads users."""
    for a in AGREEMENTS:
        if a["type"] in {"ACE", "AAP"}:
            assert a.get("scope"), f"{a['slug']} sin 'scope'"
            assert "NO es un TLC" in (a.get("notes") or ""), f"{a['slug']} sin aviso explícito"


def test_generated_markdown_is_in_sync_with_the_json():
    """docs/tlc-mexico.md is generated; it must match the current seed."""
    import subprocess

    repo = Path(seed_agreements.SEED).resolve().parents[2]
    md = repo / "docs" / "tlc-mexico.md"
    if not md.exists():
        pytest.skip("docs/tlc-mexico.md no generado aún")
    before = md.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(repo / "tools" / "gen_agreements_md.py")],
                   check=True, capture_output=True, cwd=repo)
    assert md.read_text(encoding="utf-8") == before, (
        "docs/tlc-mexico.md está desincronizado; corre python tools/gen_agreements_md.py"
    )


@pytest.mark.skipif(not seed_agreements.GEOJSON.exists(), reason="geojson no generado")
def test_every_member_iso3_is_a_known_country():
    known = seed_agreements._known_iso3()
    for a in AGREEMENTS:
        for iso3 in a["members"]:
            assert iso3 in known, f"{a['slug']}: ISO3 {iso3} no está en el catálogo de países"
