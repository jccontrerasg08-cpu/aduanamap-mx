"""Rate limiter: per-route limits, window reset, 429 semantics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from app import ratelimit  # noqa: E402


def test_route_specific_limits():
    assert ratelimit.limit_for("/api/classify/suggest") == 10
    assert ratelimit.limit_for("/api/tariff/7318") == 30
    assert ratelimit.limit_for("/api/countries/JPN") == ratelimit.DEFAULT_LIMIT


def test_blocks_after_limit_and_sets_retry_after():
    client = "test-client-1"
    path = "/api/classify/suggest"  # limit 10
    now = 1_000_000.0
    last = None
    for _ in range(10):
        last = ratelimit.check(client, path, now=now)
        assert last.allowed
    blocked = ratelimit.check(client, path, now=now)
    assert not blocked.allowed
    assert blocked.retry_after > 0
    assert blocked.remaining == 0


def test_window_resets_next_bucket():
    client = "test-client-2"
    path = "/api/classify/suggest"
    now = 2_000_000.0
    for _ in range(11):
        ratelimit.check(client, path, now=now)
    # Advance past the window → fresh allowance.
    later = ratelimit.check(client, path, now=now + ratelimit.WINDOW_SECONDS)
    assert later.allowed
