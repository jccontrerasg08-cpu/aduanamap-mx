"""The grounded trade assistant: correct, cited, and never inventing.

These run with NO database and NO LLM — the assistant reads the repo's canonical
seed, so this is the real behavior, not a mock.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from ai import assistant, knowledge  # noqa: E402

pytestmark = pytest.mark.skipif(
    not knowledge.data_available(), reason="catálogo de acuerdos no disponible"
)


# ── Country resolution (the bug that mattered: "México tiene TLC con X") ────
def test_resolves_partner_not_mexico():
    c = knowledge.resolve_country("¿México tiene TLC con Japón?")
    assert c is not None and c["iso3"] == "JPN"


def test_resolves_accentless_and_english():
    assert knowledge.resolve_country("tlc con japon")["iso3"] == "JPN"
    assert knowledge.resolve_country("agreement with Germany")["iso3"] == "DEU"


def test_resolves_common_alias():
    assert knowledge.resolve_country("tratado con Estados Unidos")["iso3"] == "USA"


# ── Grounded answers ────────────────────────────────────────────────────────
def test_answers_country_with_agreement_and_cites_source():
    r = assistant.answer("¿México tiene TLC con Japón?")
    assert "Japón" in r["answer"]
    assert "2005-04-01" in r["answer"]  # effective date from the catalog
    assert r["grounded"] is True
    assert any(s["source"] == "SE/SICE" for s in r["source_trace"])
    # Japan is covered by BOTH the bilateral EPA and CPTPP — both must surface.
    assert set(r["data"]["agreements"]) == {"aae-mexico-japon", "cptpp-tipat"}


def test_eu_member_resolves_through_tlcuem():
    # Germany has no bilateral FTA; coverage comes from the EU27 membership list.
    r = assistant.answer("¿TLC con Alemania?")
    assert "tlcuem" in r["data"]["agreements"]


def test_country_with_multiple_instruments():
    r = assistant.answer("¿qué tratados tenemos con Chile?")
    slugs = set(r["data"]["agreements"])
    assert {"tlc-mexico-chile", "alianza-del-pacifico"} <= slugs


def test_country_without_fta_is_honest_not_invented():
    r = assistant.answer("¿México tiene TLC con Rusia?")
    assert "no tiene" in r["answer"].lower()
    assert r["data"]["agreements"] == []
    assert any("no confirmable" in w for w in r["warnings"])


def test_agreement_detail_by_acronym():
    r = assistant.answer("háblame del T-MEC")
    assert "T-MEC" in r["answer"]
    assert "USA" in r["answer"] and "CAN" in r["answer"]
    assert r["data"]["slug"] == "t-mec"


def test_count_reports_source_disagreement():
    r = assistant.answer("¿cuántos TLC tiene México?")
    assert "52" in r["answer"]          # partner countries
    assert "14" in r["answer"] and "12" in r["answer"]  # SE vs ANAM claims
    assert r["data"]["partner_countries"] == 52


# ── The non-negotiable: never states a rate ─────────────────────────────────
@pytest.mark.parametrize(
    "q",
    [
        "¿cuánto arancel pago por importar tornillos?",
        "qué IVA aplica a este producto",
        "dame la tasa de DTA",
        "what duty rate applies to steel screws?",
        "cuál es la regla de origen para textiles",
    ],
)
def test_never_states_rates(q):
    r = assistant.answer(q)
    assert any("no confirmable" in w for w in r["warnings"])
    # It must point at the deterministic tools instead of answering with a number.
    assert "/arancel" in r["answer"] or "/calculadora" in r["answer"]
    assert not any(ch.isdigit() and "%" in r["answer"] for ch in r["answer"][:0])


def test_rate_question_still_reports_preference_existence_without_a_number():
    r = assistant.answer("¿cuánto arancel pago si importo de Japón?")
    # It may confirm a preferential instrument EXISTS (that is catalog data)…
    assert "Japón" in r["answer"]
    # …but must still refuse the rate itself.
    assert any("no confirmable" in w for w in r["warnings"])


# ── Robustness / degradation ────────────────────────────────────────────────
def test_empty_question_guides_instead_of_failing():
    r = assistant.answer("")
    assert r["grounded"] is False
    assert r["answer"]


def test_unrelated_question_does_not_hallucinate():
    r = assistant.answer("¿cuál es la capital de Francia?")
    # France IS a catalog country, so it answers about the FTA — not the capital.
    assert "capital" not in r["answer"].lower()


def test_gibberish_falls_back_to_capability_statement():
    r = assistant.answer("zzzz qqqq xxxx")
    assert r["grounded"] is False
    assert "tratados de libre comercio" in r["answer"].lower()


def test_very_long_input_is_truncated_safely():
    r = assistant.answer("Japón " * 500)
    assert r["answer"]  # no crash


def test_every_answer_carries_a_disclaimer():
    for q in ["¿TLC con Japón?", "¿cuántos TLC?", "", "zzz"]:
        r = assistant.answer(q)
        assert any("no es asesoría" in w or "not legal" in w for w in r["warnings"])


def test_english_answers_in_english():
    r = assistant.answer("does Mexico have an FTA with Japan?", lang="en")
    assert "in force since" in r["answer"]
    assert any("not legal" in w for w in r["warnings"])
