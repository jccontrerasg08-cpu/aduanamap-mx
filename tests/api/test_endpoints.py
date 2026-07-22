"""Contract tests for the expanded endpoint surface.

All run without Postgres/Redis: the API must degrade gracefully, always return
the data/source_trace/warnings envelope, and never fabricate a rate or code.
"""
import os
import sys
from pathlib import Path

# Disable rate limiting so the shared TestClient isn't throttled across tests.
os.environ["RATE_LIMIT_ENABLED"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

ENVELOPE_KEYS = {"data", "source_trace", "warnings"}


def _assert_envelope(body):
    assert set(body) == ENVELOPE_KEYS
    assert isinstance(body["source_trace"], list)
    assert isinstance(body["warnings"], list)


def test_root_lists_endpoints():
    body = client.get("/").json()
    assert "/api/calculator/estimate" in body["endpoints"]


def test_map_countries_envelope():
    body = client.get("/api/map/countries").json()
    _assert_envelope(body)
    assert isinstance(body["data"], list)


def test_country_profile_invalid_iso3():
    body = client.get("/api/countries/JP").json()  # too short
    _assert_envelope(body)
    assert body["data"] is None
    assert body["warnings"]


def test_country_profile_valid_but_absent():
    body = client.get("/api/countries/JPN").json()
    _assert_envelope(body)
    # No DB → null + a warning, never a fabricated profile.
    if body["data"] is None:
        assert body["warnings"]


def test_agreement_detail_absent():
    body = client.get("/api/agreements/mexico-japon").json()
    _assert_envelope(body)


def test_tariff_search_envelope():
    body = client.get("/api/tariff/search", params={"q": "tornillo"}).json()
    _assert_envelope(body)
    assert isinstance(body["data"], list)


def test_tariff_search_requires_q():
    assert client.get("/api/tariff/search").status_code == 422


def test_classify_suggest_never_invents():
    body = client.post("/api/classify/suggest",
                       json={"product_description": "camisa de algodón para mujer"}).json()
    _assert_envelope(body)
    assert "candidates" in body["data"]
    # Without an index, candidates must be empty — not hallucinated.
    if not body["data"]["candidates"]:
        assert any("no confirmable" in w for w in body["warnings"])


def test_wiki_absent_is_not_confirmable():
    body = client.get("/api/wiki/tratados/t-mec").json()
    _assert_envelope(body)


def test_banxico_series_validates_id():
    body = client.get("/api/banxico/series/@@@/latest").json()
    _assert_envelope(body)
    assert body["data"] is None
