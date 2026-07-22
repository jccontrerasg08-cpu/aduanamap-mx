"""Banxico FIX (SF43718). Fallback order per report:
API viva -> snapshot normalizado en PostgreSQL -> respuesta `stale` con timestamp
-> mensaje "temporalmente no disponible". Cache TTL 15 min."""
from __future__ import annotations

import json

from fastapi import APIRouter

from .. import cache, db
from ..config import get_settings
from ..envelope import ok

router = APIRouter(tags=["banxico"])

_CACHE_KEY = "banxico:fix:latest"
_CACHE_TTL = 15 * 60

_LATEST_FROM_DB = """
SELECT date, value, published_at
FROM exchange_rate
WHERE series_id = %s
ORDER BY date DESC
LIMIT 1
"""


@router.get("/api/banxico/fix/latest")
def fix_latest():
    settings = get_settings()

    cached = cache.get(_CACHE_KEY)
    if cached:
        payload = json.loads(cached)
        payload["status"] = "fresh"
        return ok(payload, trace=[{"source": "Banxico", "label": "SIE_API_cache"}])

    # Fallback: most recent normalized snapshot in Postgres.
    with db.connection() as conn:
        if conn is not None:
            try:
                with conn.cursor() as cur:
                    cur.execute(_LATEST_FROM_DB, (settings.banxico_fix_serie,))
                    row = cur.fetchone()
                    if row:
                        date, value, published_at = row
                        payload = {
                            "series_id": settings.banxico_fix_serie,
                            "label": "Pesos por Dólar FIX",
                            "date": date.isoformat(),
                            "value": float(value),
                            "status": "stale",
                        }
                        cache.setex(_CACHE_KEY, _CACHE_TTL, json.dumps(payload))
                        return ok(
                            payload,
                            trace=[{"source": "Banxico", "label": "snapshot_postgres"}],
                            warnings=["stale: sirviendo último snapshot; el worker actualizará el FIX"],
                        )
            except Exception:
                pass

    return ok(
        None,
        trace=[{"source": "Banxico", "label": "SIE_API"}],
        warnings=["Banxico FIX temporalmente no disponible. Ejecuta el worker banxico_fix o valida en el SIE."],
    )
