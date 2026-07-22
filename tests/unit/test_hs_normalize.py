"""Normalization of a 10-digit MX code into HS hierarchy levels.

Product rule: HS (6) is universal; Fracción (8) + NICO (10) is national.
This helper is deterministic — no LLM ever touches classification math.
"""


def normalize_code(code: str) -> dict:
    digits = "".join(c for c in code if c.isdigit())
    out = {"input": code}
    if len(digits) >= 2:
        out["hs2"] = digits[:2]
    if len(digits) >= 4:
        out["hs4"] = digits[:4]
    if len(digits) >= 6:
        out["hs6"] = digits[:6]
    if len(digits) >= 8:
        out["fraccion8"] = digits[:8]
    if len(digits) == 10:
        out["nico10"] = digits
    return out


def test_full_nico():
    out = normalize_code("7318159900")
    assert out["hs2"] == "73"
    assert out["hs4"] == "7318"
    assert out["hs6"] == "731815"
    assert out["fraccion8"] == "73181599"
    assert out["nico10"] == "7318159900"


def test_partial_hs6_only():
    out = normalize_code("7318.15")
    assert out["hs6"] == "731815"
    assert "fraccion8" not in out
