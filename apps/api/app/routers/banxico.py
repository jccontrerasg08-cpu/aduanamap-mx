"""Banxico FIX (SF43718). Fallback order per report:
API viva -> snapshot normalizado en PostgreSQL -> respuesta `stale` con timestamp
-> mensaje "temporalmente no disponible". Cache TTL 15 min."""
from __future__ import annotations

import json
import re

from fastapi import APIRouter

from .. import cache, db
from ..config import get_settings
from ..envelope import ok

router = APIRouter(tags=["banxico"])

_CACHE_KEY = "banxico:fix:latest"
_CACHE_TTL = 15 * 60
_SERIES_RE = re.compile(r"^[A-Za-z]{2}\d{1,8}$")

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


@router.get("/api/banxico/series/{series_id}/latest")
def series_latest(series_id: str):
    """Último dato de una serie del SIE almacenada en exchange_rate."""
    if not _SERIES_RE.match(series_id):
        return ok(None, warnings=["series_id inválido (formato SIE, p.ej. SF43718)"])
    series_id = series_id.upper()
    with db.connection() as conn:
        if conn is None:
            return ok(None, warnings=["stale: base de datos no disponible"])
        try:
            with conn.cursor() as cur:
                cur.execute(_LATEST_FROM_DB, (series_id,))
                row = cur.fetchone()
                if row is None:
                    return ok(None, warnings=[f"no confirmable: serie {series_id} sin datos cargados"])
                date, value, _published = row
        except Exception:
            return ok(None, warnings=["stale: series Banxico aún no cargadas"])
    return ok({"series_id": series_id, "date": date.isoformat(), "value": float(value)},
              trace=[{"source": "Banxico", "label": "SIE_API"}])
