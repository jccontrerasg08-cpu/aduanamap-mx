"""The domain registry: discovery by convention, and failure isolation.

This is the plumbing that lets many independent customs topics be added without
editing any shared file. It must (a) discover valid modules, (b) never be taken
down by a broken one, and (c) never let a domain override the assistant's
existing correct behavior or its refusal to state rates.
"""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from ai import assistant, domains  # noqa: E402

DOMAINS_DIR = Path(domains.__path__[0])


@pytest.fixture
def temp_domain():
    """Write a domain module into ai/domains/, then remove it."""
    created: list[Path] = []

    def _make(name: str, body: str) -> None:
        p = DOMAINS_DIR / f"{name}.py"
        p.write_text(textwrap.dedent(body), encoding="utf-8")
        created.append(p)
        domains.reset()

    yield _make
    for p in created:
        p.unlink(missing_ok=True)
        sys.modules.pop(f"ai.domains.{p.stem}", None)
    domains.reset()


def test_registry_survives_with_no_domains():
    domains.reset()
    assert isinstance(domains.discover(), list)
    assert isinstance(domains.names(), list)


def test_template_is_not_discovered():
    """TEMPLATE.py.txt must not be importable/registered."""
    assert (DOMAINS_DIR / "TEMPLATE.py.txt").exists()
    assert "mi_tema" not in domains.names()


def test_discovers_a_valid_domain_and_routes_to_it(temp_domain):
    temp_domain("zz_probe", '''
        NAME = "zz_probe"
        SEED = "zz_probe.json"
        def match(q):
            return "xyzzy" in q.lower()
        def answer(q, lang="es"):
            return {"answer": "respuesta de prueba",
                    "data": {"ok": True},
                    "sources": [{"source": "SNICE", "label": "prueba"}]}
    ''')
    assert "zz_probe" in domains.names()
    routed = domains.try_answer("dime algo de xyzzy")
    assert routed is not None
    assert routed["answer"] == "respuesta de prueba"
    assert routed["domain"] == "zz_probe"

    # End to end through the assistant, with the domain's own citation.
    r = assistant.answer("dime algo de xyzzy")
    assert r["answer"] == "respuesta de prueba"
    assert any(s["source"] == "SNICE" for s in r["source_trace"])


def test_broken_domain_is_skipped_not_fatal(temp_domain):
    temp_domain("zz_broken", "raise RuntimeError('boom')")
    # Discovery still works and the assistant still answers.
    assert "zz_broken" not in domains.names()
    assert assistant.answer("¿TLC con Japón?")["grounded"] is True


def test_domain_with_broken_matcher_is_skipped(temp_domain):
    temp_domain("zz_badmatch", '''
        NAME = "zz_badmatch"
        SEED = "x.json"
        def match(q):
            raise ValueError("bad matcher")
        def answer(q, lang="es"):
            return {"answer": "nope"}
    ''')
    assert domains.try_answer("cualquier cosa") is None


def test_incomplete_domain_is_rejected(temp_domain):
    temp_domain("zz_partial", 'NAME = "zz_partial"\nSEED = "x.json"\n')  # no match/answer
    assert "zz_partial" not in domains.names()


def test_domain_cannot_answer_a_rate_question(temp_domain):
    """The rate refusal runs BEFORE the registry — no domain may quote a rate."""
    temp_domain("zz_rate", '''
        NAME = "zz_rate"
        SEED = "x.json"
        def match(q):
            return True
        def answer(q, lang="es"):
            return {"answer": "El arancel es 15%"}
    ''')
    r = assistant.answer("¿cuánto arancel pago por tornillos?")
    assert "15%" not in r["answer"]
    assert any("no confirmable" in w for w in r["warnings"])


def test_domain_cannot_override_existing_fta_behavior(temp_domain):
    temp_domain("zz_greedy", '''
        NAME = "zz_greedy"
        SEED = "x.json"
        PRIORITY = 1
        def match(q):
            return True
        def answer(q, lang="es"):
            return {"answer": "SECUESTRADO"}
    ''')
    r = assistant.answer("¿México tiene TLC con Japón?")
    assert "SECUESTRADO" not in r["answer"]
    assert "Japón" in r["answer"]


def test_domain_output_is_still_scrubbed(temp_domain):
    temp_domain("zz_leak", '''
        NAME = "zz_leak"
        SEED = "x.json"
        def match(q):
            return "leakprobe" in q
        def answer(q, lang="es"):
            return {"answer": "config DATABASE_URL=postgres://u:p@h/db"}
    ''')
    r = assistant.answer("leakprobe")
    assert "postgres://" not in r["answer"]
    assert "[redactado]" in r["answer"]


def test_load_seed_missing_file_returns_empty():
    from ai import knowledge
    assert knowledge.load_seed("definitely-not-a-real-seed-file.json") == {}
