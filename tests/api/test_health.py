"""Smoke tests for the API envelope + ops endpoints.

Run: cd apps/api && pip install -e .[dev] && pytest ../../tests/api
The app degrades gracefully, so these pass even without Postgres/Redis running.
"""
import sys
from pathlib import Path

# Make the api app importable regardless of CWD.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_healthz_shape():
    r = client.get("/api/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    assert set(body["dependencies"]) == {"postgres", "redis"}


def test_sources_status_envelope():
    r = client.get("/api/sources/status")
    assert r.status_code == 200
    body = r.json()
    # Every response follows the data / source_trace / warnings envelope.
    assert set(body) == {"data", "source_trace", "warnings"}
    assert isinstance(body["data"], list)


def test_banxico_fix_never_invents():
    r = client.get("/api/banxico/fix/latest")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"data", "source_trace", "warnings"}
    # With no cache/DB the value must be null with a warning — never a fabricated rate.
    if body["data"] is None:
        assert body["warnings"]
