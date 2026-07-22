"""Página wiki renderizable (contenido editorial bilingüe)."""
from __future__ import annotations

import re

from fastapi import APIRouter, Query

from .. import db
from ..envelope import ok

router = APIRouter(tags=["wiki"])

_SLUG_RE = re.compile(r"^[a-z0-9/_-]{1,120}$")

_WIKI_Q = """
SELECT slug, kind, lang, title, summary, body_md, last_verified_at
FROM wiki_page
WHERE slug = %s AND lang = %s AND status = 'published'
LIMIT 1
"""


@router.get("/api/wiki/{slug:path}")
def wiki_page(slug: str, lang: str = Query("es")):
    if not _SLUG_RE.match(slug) or lang not in {"es", "en"}:
        return ok(None, warnings=["parámetros inválidos (slug o lang)"])
    with db.connection() as conn:
        if conn is None:
            return ok(None, warnings=["stale: base de datos no disponible"])
        try:
            with conn.cursor() as cur:
                cur.execute(_WIKI_Q, (slug, lang))
                row = cur.fetchone()
                if row is None:
                    return ok(None, warnings=[f"no confirmable: página '{slug}' ({lang}) no publicada"])
                s, kind, lg, title, summary, body_md, verified = row
        except Exception:
            return ok(None, warnings=["stale: contenido editorial aún no cargado"])
    data = {
        "slug": s, "kind": kind, "lang": lg, "title": title,
        "summary": summary, "body_md": body_md,
        "last_verified_at": verified.isoformat() if verified else None,
    }
    return ok(data, trace=[{"source": "wiki_page", "label": "editorial"},
                           {"source": "agreement_document", "label": "source_docs"}])
