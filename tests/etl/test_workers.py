"""ETL worker robustness: snapshot hashing, SIE parsing, HTTP retry/backoff."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workers import banxico_fix  # noqa: E402
from workers.common import http, manifest  # noqa: E402


def test_sha256_is_deterministic():
    a = manifest.sha256_bytes(b"hola aduana")
    b = manifest.sha256_bytes(b"hola aduana")
    assert a == b and len(a) == 64


def test_parse_sie_oportuno_payload():
    payload = (b'{"bmx":{"series":[{"idSerie":"SF43718",'
               b'"datos":[{"fecha":"03/07/2026","dato":"18.7342"}]}]}}')
    parsed = banxico_fix.parse(payload)
    assert parsed == ("2026-07-03", 18.7342)


def test_parse_rejects_bad_payload():
    assert banxico_fix.parse(b"<html>maintenance</html>") is None


def test_dry_run_without_token(monkeypatch, capsys):
    monkeypatch.setattr(banxico_fix, "TOKEN", "")
    assert banxico_fix.run() == 0
    assert "DRY-RUN" in capsys.readouterr().out


def test_http_retries_then_gives_up(monkeypatch):
    """No httpx / hard failure → fetch returns None without raising."""
    monkeypatch.setattr(http.time, "sleep", lambda *_: None)  # don't actually wait
    calls = {"n": 0}

    class _Boom(Exception):
        pass

    class _FakeHttpx:
        @staticmethod
        def get(*a, **k):
            calls["n"] += 1
            raise _Boom("down")

    monkeypatch.setitem(sys.modules, "httpx", _FakeHttpx)
    assert http.fetch("https://example.test/x", max_attempts=3) is None
    assert calls["n"] == 3  # retried the configured number of times
