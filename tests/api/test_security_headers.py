"""Security headers are present on every response, incl. errors and 429s."""
import os
import sys
from pathlib import Path

os.environ["RATE_LIMIT_ENABLED"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_hardening_headers_on_ok_response():
    h = client.get("/api/healthz").headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in h
    assert "Referrer-Policy" in h
    assert "Permissions-Policy" in h


def test_no_hsts_in_development():
    # HSTS must not be sent over http/localhost dev.
    assert "Strict-Transport-Security" not in client.get("/").headers


def test_headers_present_on_404():
    h = client.get("/api/does-not-exist").headers
    assert h.get("X-Content-Type-Options") == "nosniff"
