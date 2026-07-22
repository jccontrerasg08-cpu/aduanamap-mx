"""Calculator: deterministic customs value, never-invented duties."""
import os
import sys
from pathlib import Path

os.environ["RATE_LIMIT_ENABLED"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import calculator  # noqa: E402

client = TestClient(app)


def test_estimate_validates_negative_invoice():
    r = client.post("/api/calculator/estimate",
                    json={"invoice_value": -5, "input_code": "84713001"})
    assert r.status_code == 422


def test_estimate_without_fix_is_not_confirmable():
    body = client.post("/api/calculator/estimate",
                       json={"invoice_value": 10000, "freight": 900, "insurance": 100,
                             "incoterm": "CIF", "input_code": "84713001"}).json()
    data = body["data"]
    # No FIX loaded → duties null, preferential not_confirmable, no fabricated numbers.
    assert data["preferential_treatment"] == "not_confirmable"
    assert data["estimated_igi_mxn"] is None


def test_customs_value_is_deterministic_when_rate_present(monkeypatch):
    """With a stubbed FIX and no tariff rate: customs value computes, duties stay null."""
    from decimal import Decimal

    class _Cur:
        def __init__(self): self._q = None
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, q, params=None): self._q = q
        def fetchone(self):
            if "exchange_rate" in self._q:
                return ("2026-07-03", Decimal("18.50"))
            return None  # no tariff_rate row

    class _Conn:
        def cursor(self): return _Cur()

    class _CM:
        def __enter__(self): return _Conn()
        def __exit__(self, *a): return False

    monkeypatch.setattr(calculator.db, "connection", lambda: _CM())
    data, _trace, _warns = calculator.estimate(
        {"invoice_value": 1000, "freight": 0, "insurance": 0, "incoterm": "FOB",
         "input_code": "84713001"})
    # FOB → customs base = invoice + freight + insurance = 1000; ×18.50 = 18500.
    assert data["customs_value_mxn"] == 18500.0
    assert data["estimated_igi_mxn"] is None  # never invented without a rate
