"""Source divergence: an authoritative source can be stale, and we must not follow it.

ANAM's public listing (captured 2026-07-24) still shows TLCAN, Venezuela in the G3
and the UK inside TLCUEM. The canonical catalog must answer with what is CURRENTLY in
force, while still being able to report what ANAM says — with the caveat.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from ai import assistant, knowledge  # noqa: E402

pytestmark = pytest.mark.skipif(
    knowledge.get_source_listing("ANAM") is None, reason="listado ANAM no registrado"
)


def test_anam_listing_is_recorded_verbatim_with_divergences():
    anam = knowledge.get_source_listing("ANAM")
    assert anam["consulted_at"]
    assert anam["url"].startswith("https://www.anam.gob.mx")
    assert len(anam["listed_instruments"]) == 12  # ANAM's own count
    assert len(anam["divergences_vs_canonical"]) >= 8
    assert "desactualizado" in anam["assessment"]


def test_canonical_catalog_is_not_polluted_by_the_stale_listing():
    """The stale entries must NOT appear as active instruments in the catalog."""
    active_slugs = {a["slug"] for a in knowledge.ftas(active_only=True)}
    # TLCAN is superseded by T-MEC; the Bolivia FTA by ACE 66.
    assert "t-mec" in active_slugs
    assert not any("tlcan" in s for s in active_slugs)
    assert "tlc-mexico-bolivia-1995" not in active_slugs


def test_venezuela_is_not_reported_as_having_an_fta():
    """ANAM lists Venezuela in the G3; it withdrew in 2006."""
    r = assistant.answer("¿México tiene TLC con Venezuela?")
    assert r["data"]["agreements"] == []
    assert "no tiene" in r["answer"].lower()


def test_uk_resolves_via_cptpp_not_tlcuem():
    """ANAM lists the UK inside TLCUEM; post-Brexit its link is CPTPP (2024)."""
    r = assistant.answer("¿TLC con Reino Unido?")
    assert r["data"]["agreements"] == ["cptpp-tipat"]
    assert "tlcuem" not in r["data"]["agreements"]


def test_eu_has_27_not_25_members():
    eu = next(a for a in knowledge.ftas() if a["slug"] == "tlcuem")
    assert len(eu["members"]) == 27
    assert "GBR" not in eu["members"]      # left the EU
    assert {"BGR", "ROU", "HRV"} <= set(eu["members"])  # ANAM's list omitted these


def test_assistant_can_report_what_anam_says_with_the_caveat():
    r = assistant.answer("¿qué dice ANAM sobre los tratados?")
    assert "ANAM" in r["answer"]
    assert "12 TLC" in r["answer"]
    assert "desactualizado" in r["answer"]
    assert r["data"]["divergences"]


def test_anam_appri_examples_are_captured():
    anam = knowledge.get_source_listing("ANAM")
    partners = {a["partner"] for a in anam["appri_examples"]}
    assert {"NLD", "ESP", "FIN"} <= partners
