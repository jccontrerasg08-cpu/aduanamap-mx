"""Landed-cost estimator.

Split into what is *deterministic* and what is *not confirmable*:

  - Customs value (valor en aduana) in MXN is arithmetic from the user's inputs
    and the official FIX, so it is computed and returned.
  - IGI / DTA / IVA and preferential treatment depend on a structured rate and a
    verified rule of origin. If those rows are absent, the estimator returns
    `null` for each and marks preferential_treatment = "not_confirmable" — it
    never guesses a duty. This is the report's single hardest product rule.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .. import db

# Incoterms where freight/insurance are already included in the transaction value
# the buyer pays. CIF-family → customs value ≈ invoice (already landed to border);
# EXW/FOB-family → add freight + insurance to approximate the CIF customs base.
_CIF_LIKE = {"CIF", "CIP", "DAP", "DDP", "CFR", "CPT"}

_FIX_Q = """
SELECT date, value FROM exchange_rate
WHERE series_id = %s ORDER BY date DESC LIMIT 1
"""

_RATE_Q = """
SELECT import_rate, rate_type, effective_from
FROM tariff_rate
WHERE target_code = %s AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
ORDER BY effective_from DESC LIMIT 1
"""


def _d(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def estimate(payload: dict, *, fix_serie: str = "SF43718") -> tuple[dict, list[dict], list[str]]:
    warnings: list[str] = []
    trace: list[dict] = [{"source": "agreement", "label": "country_relation"}]

    invoice = _d(payload.get("invoice_value"))
    freight = _d(payload.get("freight"))
    insurance = _d(payload.get("insurance"))
    incoterm = str(payload.get("incoterm", "")).upper()
    code = "".join(c for c in str(payload.get("input_code", "")) if c.isdigit())

    # ── Exchange rate (FIX) ──────────────────────────────────────────────────
    rate = None
    with db.connection() as conn:
        if conn is not None:
            try:
                with conn.cursor() as cur:
                    cur.execute(_FIX_Q, (fix_serie,))
                    row = cur.fetchone()
                    if row:
                        rate = _d(row[1])
                        trace.append({"source": "Banxico", "label": "FIX"})
            except Exception:
                pass

    if rate is None or rate == 0:
        warnings.append("no confirmable: sin tipo de cambio FIX; ejecuta el worker banxico_fix")
        return (
            {"mxn_exchange_rate": None, "customs_value_mxn": None,
             "estimated_igi_mxn": None, "estimated_dta_mxn": None, "estimated_iva_mxn": None,
             "preferential_treatment": "not_confirmable",
             "explanation": "Falta tipo de cambio FIX para convertir el valor en aduana."},
            trace, warnings,
        )

    # ── Customs value (deterministic) ────────────────────────────────────────
    base_foreign = invoice if incoterm in _CIF_LIKE else invoice + freight + insurance
    customs_value_mxn = (base_foreign * rate).quantize(Decimal("0.01"))

    # ── Duties (never invented) ──────────────────────────────────────────────
    import_rate = None
    with db.connection() as conn:
        if conn is not None and code:
            try:
                with conn.cursor() as cur:
                    cur.execute(_RATE_Q, (code,))
                    r = cur.fetchone()
                    if r and r[0] is not None:
                        import_rate = _d(r[0])
                        trace.append({"source": "LIGIE/tariff_rate", "label": r[1]})
            except Exception:
                pass

    igi = dta = iva = None
    preferential = "not_confirmable"
    if import_rate is not None:
        igi = (customs_value_mxn * import_rate / Decimal("100")).quantize(Decimal("0.01"))
        explanation = "IGI calculado desde tasa estructurada vigente; validar regla de origen."
    else:
        explanation = ("Falta validación estructurada de tasa vigente y regla de origen. "
                       "El sistema no estima aranceles sin fuente.")
        warnings.append("no confirmable: sin tasa estructurada para la fracción; IGI/DTA/IVA no calculados")

    data = {
        "mxn_exchange_rate": float(rate),
        "customs_value_mxn": float(customs_value_mxn),
        "estimated_igi_mxn": float(igi) if igi is not None else None,
        "estimated_dta_mxn": float(dta) if dta is not None else None,
        "estimated_iva_mxn": float(iva) if iva is not None else None,
        "preferential_treatment": preferential,
        "explanation": explanation,
    }
    warnings.append("Estimación informativa. No sustituye cálculo legal ni pedimento.")
    return data, trace, warnings
