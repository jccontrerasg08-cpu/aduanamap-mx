"""Tariff explorer: deterministic normalization + never-invent lookup contract."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_normalize_full_nico():
    r = client.get("/api/tariff/normalize/7318.15.99.00")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["hs2"] == "73"
    assert data["hs6"] == "731815"
    assert data["fraccion8"] == "73181599"
    assert data["nico10"] == "7318159900"


def test_normalize_hs6_only_has_no_fraccion():
    data = client.get("/api/tariff/normalize/7318.15").json()["data"]
    assert data["hs6"] == "731815"
    assert "fraccion8" not in data


def test_resolve_envelope_and_never_invents():
    r = client.get("/api/tariff/7318159900")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"data", "source_trace", "warnings"}
    # Deterministic breakdown is always present…
    assert body["data"]["normalize"]["hs6"] == "731815"
    # …but with no catalog loaded, catalog fields stay null + flagged, never faked.
    if body["data"]["fraccion"] is None:
        assert any(w.startswith("no confirmable") for w in body["warnings"])
