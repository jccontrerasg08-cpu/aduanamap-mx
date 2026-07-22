"""ETL / source freshness — makes operation visible to the public.
Reads latest etl_run per source; degrades to empty list if DB is down."""
from __future__ import annotations

from fastapi import APIRouter

from .. import db
from ..envelope import ok

router = APIRouter(tags=["ops"])

_QUERY = """
SELECT DISTINCT ON (source_name)
       source_name, status, finished_at
FROM etl_run
ORDER BY source_name, started_at DESC
"""


@router.get("/api/sources/status")
def sources_status():
    rows = []
    warnings: list[str] = []
    with db.connection() as conn:
        if conn is None:
            warnings.append("stale: base de datos no disponible; mostrando lista vacía")
        else:
            try:
                with conn.cursor() as cur:
                    cur.execute(_QUERY)
                    for source_name, status, finished_at in cur.fetchall():
                        rows.append({
                            "source": source_name,
                            "status": status,
                            "last_success": finished_at.isoformat() if finished_at else None,
                        })
            except Exception:
                warnings.append("stale: aún no hay corridas ETL registradas")
    return ok(rows, trace=[{"source": "etl_run", "label": "latest_runs"}], warnings=warnings)
