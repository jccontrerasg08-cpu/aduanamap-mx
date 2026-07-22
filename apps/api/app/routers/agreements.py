"""Ficha de tratado/acuerdo. Degrada a `no confirmable` si no existe el slug."""
from __future__ import annotations

import re

from fastapi import APIRouter, Query

from .. import db
from ..envelope import ok

router = APIRouter(tags=["agreements"])

_SLUG_RE = re.compile(r"^[a-z0-9-]{1,80}$")

_AGREEMENT_Q = """
SELECT a.slug, a.name_es, a.name_en, a.type, a.status, a.signed_date, a.effective_date
FROM agreement a WHERE a.slug = %s
"""

_MEMBERS_Q = """
SELECT c.iso3
FROM agreement_member am
JOIN agreement a ON a.id = am.agreement_id
JOIN country c ON c.id = am.country_id
WHERE a.slug = %s
ORDER BY c.iso3
"""

_DOCS_Q = """
SELECT ad.title, ad.document_type, ad.id::text
FROM agreement_document ad
JOIN agreement a ON a.id = ad.agreement_id
WHERE a.slug = %s
ORDER BY ad.effective_date NULLS LAST
"""


@router.get("/api/agreements/{slug}")
def agreement_detail(slug: str, lang: str = Query("es")):
    if not _SLUG_RE.match(slug):
        return ok(None, warnings=["slug inválido: usar minúsculas, dígitos y guiones"])
    with db.connection() as conn:
        if conn is None:
            return ok(None, warnings=["stale: base de datos no disponible"])
        try:
            with conn.cursor() as cur:
                cur.execute(_AGREEMENT_Q, (slug,))
                row = cur.fetchone()
                if row is None:
                    return ok(None, warnings=[f"no confirmable: tratado '{slug}' sin registro"])
                s, name_es, name_en, type_, status, signed, eff = row
                cur.execute(_MEMBERS_Q, (slug,))
                members = [r[0] for r in cur.fetchall()]
                cur.execute(_DOCS_Q, (slug,))
                docs = [{"title": t, "kind": k, "document_id": did} for t, k, did in cur.fetchall()]
        except Exception:
            return ok(None, warnings=["stale: catálogo de tratados aún no cargado"])
    data = {
        "slug": s,
        "name": name_en if lang == "en" else name_es,
        "type": type_, "status": status,
        "members": members,
        "signed_date": signed.isoformat() if signed else None,
        "effective_date": eff.isoformat() if eff else None,
        "documents": docs,
    }
    return ok(data, trace=[{"source": "SNICE", "label": "biblioteca_juridica_tlc"},
                           {"source": "DOF", "label": "publicacion_relacionada"}])
