"""País y mapa mundial. Todo degrada a lista vacía + warning si la DB está caída;
nunca lanza 500 por ausencia de datos (el catálogo se llena vía workers)."""
from __future__ import annotations

import re

from fastapi import APIRouter, Query

from .. import db
from ..envelope import ok

router = APIRouter(tags=["geo"])

_ISO3_RE = re.compile(r"^[A-Za-z]{3}$")

_MAP_Q = """
SELECT c.iso3, c.name_es, c.name_en, COUNT(am.agreement_id) AS agreements_count
FROM country c
LEFT JOIN agreement_member am ON am.country_id = c.id
WHERE c.active
GROUP BY c.iso3, c.name_es, c.name_en
ORDER BY c.iso3
"""

_COUNTRY_Q = """
SELECT iso2, iso3, name_es, name_en, region, subregion
FROM country WHERE iso3 = %s
"""

_COUNTRY_AGREEMENTS_Q = """
SELECT a.slug, a.name_es, a.name_en, a.type, a.status, a.effective_date
FROM agreement a
JOIN agreement_member am ON am.agreement_id = a.id
JOIN country c ON c.id = am.country_id
WHERE c.iso3 = %s
ORDER BY a.effective_date NULLS LAST
"""


def _lang_name(lang: str, es: str, en: str) -> str:
    return en if lang == "en" else es


@router.get("/api/map/countries")
def map_countries(layer: str = Query("all"), lang: str = Query("es")):
    rows: list[dict] = []
    warnings: list[str] = []
    with db.connection() as conn:
        if conn is None:
            warnings.append("stale: catálogo de países no disponible (base de datos caída)")
        else:
            try:
                with conn.cursor() as cur:
                    cur.execute(_MAP_Q)
                    for iso3, name_es, name_en, count in cur.fetchall():
                        rows.append({
                            "iso3": iso3,
                            "name": _lang_name(lang, name_es, name_en),
                            "layer": layer,
                            "agreements_count": count,
                        })
            except Exception:
                warnings.append("stale: aún no se han cargado países ni geometrías")
    if not rows and not warnings:
        warnings.append("stale: catálogo vacío; ejecuta el importador de países/geometrías")
    return ok(rows, trace=[{"source": "SE", "label": "tratados_y_acuerdos"},
                           {"source": "country_geometry", "label": "catalogo"}], warnings=warnings)


@router.get("/api/countries/{iso3}")
def country_profile(iso3: str, lang: str = Query("es")):
    if not _ISO3_RE.match(iso3):
        return ok(None, warnings=["iso3 inválido: se esperan 3 letras (p.ej. JPN)"])
    iso3 = iso3.upper()
    warnings: list[str] = []
    with db.connection() as conn:
        if conn is None:
            return ok(None, warnings=["stale: base de datos no disponible"])
        try:
            with conn.cursor() as cur:
                cur.execute(_COUNTRY_Q, (iso3,))
                row = cur.fetchone()
                if row is None:
                    return ok(None, warnings=[f"no confirmable: país {iso3} sin registro en catálogo"])
                iso2, iso3_, name_es, name_en, region, subregion = row
                cur.execute(_COUNTRY_AGREEMENTS_Q, (iso3,))
                slugs = [r[0] for r in cur.fetchall()]
        except Exception:
            return ok(None, warnings=["stale: catálogo de países aún no cargado"])
    data = {
        "iso2": iso2, "iso3": iso3_,
        "name": _lang_name(lang, name_es, name_en),
        "region": region, "subregion": subregion,
        "has_preferential_agreement": bool(slugs),
        "agreements": slugs,
        "country_page_slug": f"pais/{iso3.lower()}",
    }
    return ok(data, trace=[{"source": "SRE", "label": "tratados_mexico"},
                           {"source": "SNICE", "label": "biblioteca_juridica_tlc"}], warnings=warnings)


@router.get("/api/countries/{iso3}/agreements")
def country_agreements(iso3: str, lang: str = Query("es")):
    if not _ISO3_RE.match(iso3):
        return ok([], warnings=["iso3 inválido: se esperan 3 letras (p.ej. JPN)"])
    iso3 = iso3.upper()
    rows: list[dict] = []
    with db.connection() as conn:
        if conn is None:
            return ok([], warnings=["stale: base de datos no disponible"])
        try:
            with conn.cursor() as cur:
                cur.execute(_COUNTRY_AGREEMENTS_Q, (iso3,))
                for slug, name_es, name_en, type_, status, eff in cur.fetchall():
                    rows.append({
                        "slug": slug,
                        "name": _lang_name(lang, name_es, name_en),
                        "type": type_, "status": status,
                        "effective_date": eff.isoformat() if eff else None,
                    })
        except Exception:
            return ok([], warnings=["stale: acuerdos aún no cargados"])
    return ok(rows,
              trace=[{"source": "ANAM", "label": "tratados_con_mexico"},
                     {"source": "SNICE", "label": "biblioteca_juridica_tlc"}],
              warnings=["El conteo total de TLC puede variar según la fuente oficial (SE vs ANAM)."])
