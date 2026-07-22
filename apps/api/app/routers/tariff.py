"""Explorador arancelario — HS / Fracción / NICO.

Ruta determinista: nunca inventa descripciones, tasas ni preferencias. Cuando un
nivel no existe en el catálogo versionado, la respuesta lo marca `no confirmable`
y muestra la fuente primaria para validación humana (ADR 0002).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from ..envelope import ok
from ..services import search, tariff

router = APIRouter(tags=["arancel"])


@router.get("/api/tariff/normalize/{code}")
def normalize(code: str):
    """Desglose determinista de un código en HS2/HS4/HS6/Fracción8/NICO10.

    Puramente aritmético (no toca la base): útil incluso sin catálogo cargado.
    """
    return ok(tariff.normalize_code(code),
              trace=[{"source": "OMA/HS", "label": "regla_estructural"}])


# Debe declararse ANTES de /api/tariff/{code}, o "search" se captura como código.
@router.get("/api/tariff/search")
def search_tariff(q: str = Query(..., min_length=1, max_length=120),
                  lang: str = Query("es"), limit: int = Query(5, ge=1, le=50)):
    """Búsqueda por texto o código contra el índice full-text (tsvector)."""
    rows, index_available = search.search(q, lang=lang, kinds=("hs", "fraccion", "nico"), limit=limit)
    warnings = ["Resultado informativo; no sustituye una determinación legal de clasificación."]
    if not index_available:
        warnings.append("no confirmable: índice arancelario no disponible; ejecuta importadores SNICE/VUCEM")
    data = [{"display_code": r["entity_id"], "level": r["kind"],
             "description": r["title"], "score": r["score"]} for r in rows]
    return ok(data, trace=[{"source": "WCO/WITS", "label": "hs_reference"},
                           {"source": "VUCEM", "label": "clasificador_tigie"},
                           {"source": "SNICE", "label": "nico_ligie"}], warnings=warnings)


@router.get("/api/tariff/{code}")
def resolve(code: str):
    """Resuelve un código contra las tablas versionadas (hs_code/fracción/NICO)."""
    data, trace, warnings = tariff.lookup(code)
    return ok(data, trace=trace, warnings=warnings)
