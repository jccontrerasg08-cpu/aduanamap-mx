"""Tariff code resolution: HS (6, universal) → Fracción (8) → NICO (10, nacional).

Two responsibilities, kept strictly separate:

  1. normalize_code() — PURE, deterministic parsing of a code string into its
     hierarchical levels. No I/O, no LLM. This is the "lo universal es HS; lo
     nacional es TIGIE/NICO" rule expressed in code.

  2. lookup()        — read-only queries against the versioned tables
     (hs_code, mx_tariff_fraction, mx_nico). When a level has no row, the result
     is marked `not_confirmable` and the primary source is surfaced — never a
     fabricated description, rate, or preference (report non-negotiable / ADR 0002).
"""
from __future__ import annotations

from .. import db


def normalize_code(code: str) -> dict:
    """Split a code into HS2/HS4/HS6/Fracción8/NICO10. Deterministic, no I/O."""
    digits = "".join(c for c in code if c.isdigit())
    out: dict[str, str] = {"input": code, "digits": digits}
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


_HS6_Q = """
SELECT hs_version, description_es, description_en
FROM hs_code
WHERE hs6 = %s
ORDER BY hs_version DESC
LIMIT 1
"""

_FRACCION_Q = """
SELECT ligie_version, description_es, unit, effective_from, effective_to
FROM mx_tariff_fraction
WHERE fraccion8 = %s AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
ORDER BY effective_from DESC
LIMIT 1
"""

_NICO_Q = """
SELECT description_es, effective_from, effective_to
FROM mx_nico
WHERE nico10 = %s AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
ORDER BY effective_from DESC
LIMIT 1
"""


def lookup(code: str) -> tuple[dict, list[dict], list[str]]:
    """Resolve a code against versioned tables.

    Returns (data, source_trace, warnings). `data` always contains the
    deterministic `normalize` breakdown, so the response is useful even when the
    catalog has no matching row yet.
    """
    levels = normalize_code(code)
    data: dict = {"normalize": levels, "hs6": None, "fraccion": None, "nico": None}
    trace: list[dict] = []
    warnings: list[str] = []

    with db.connection() as conn:
        if conn is None:
            warnings.append("no confirmable: catálogo arancelario no disponible (base de datos caída)")
            return data, trace, warnings

        try:
            with conn.cursor() as cur:
                if levels.get("hs6"):
                    cur.execute(_HS6_Q, (levels["hs6"],))
                    row = cur.fetchone()
                    if row:
                        data["hs6"] = {"hs_version": row[0], "description_es": row[1],
                                       "description_en": row[2]}
                        trace.append({"source": "WCO/SNICE", "label": f"hs_code:{row[0]}"})

                if levels.get("fraccion8"):
                    cur.execute(_FRACCION_Q, (levels["fraccion8"],))
                    row = cur.fetchone()
                    if row:
                        data["fraccion"] = {
                            "ligie_version": row[0], "description_es": row[1], "unit": row[2],
                            "effective_from": row[3].isoformat() if row[3] else None,
                            "effective_to": row[4].isoformat() if row[4] else None,
                        }
                        trace.append({"source": "SNICE", "label": f"ligie:{row[0]}"})

                if levels.get("nico10"):
                    cur.execute(_NICO_Q, (levels["nico10"],))
                    row = cur.fetchone()
                    if row:
                        data["nico"] = {
                            "description_es": row[0],
                            "effective_from": row[1].isoformat() if row[1] else None,
                            "effective_to": row[2].isoformat() if row[2] else None,
                        }
                        trace.append({"source": "SNICE", "label": "nico"})
        except Exception:
            warnings.append("no confirmable: aún no hay catálogo cargado; ejecuta el importador SNICE")
            return data, trace, warnings

    # Surface exactly which requested levels could not be confirmed.
    if levels.get("hs6") and data["hs6"] is None:
        warnings.append(f"no confirmable: HS6 {levels['hs6']} sin registro; validar en SNICE/WCO")
    if levels.get("fraccion8") and data["fraccion"] is None:
        warnings.append(f"no confirmable: fracción {levels['fraccion8']} sin registro; validar en SNICE")
    if levels.get("nico10") and data["nico"] is None:
        warnings.append(f"no confirmable: NICO {levels['nico10']} sin registro; validar en SNICE")

    return data, trace, warnings
