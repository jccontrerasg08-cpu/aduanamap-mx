"""Sugerencia de clasificación (capa IA estrecha).

Frontera ADR 0002: SUGIERE candidatos desde el corpus indexado con `confidence`
y "por qué"; NUNCA calcula tasas ni afirma clasificación definitiva. Sin corpus
indexado devuelve lista vacía + advertencia, jamás un candidato inventado.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..envelope import ok
from ..services import search

router = APIRouter(tags=["clasificacion"])


class SuggestRequest(BaseModel):
    lang: str = Field("es", max_length=2)
    product_description: str = Field(..., min_length=3, max_length=500)
    country_origin: Optional[str] = Field(None, max_length=3)


@router.post("/api/classify/suggest")
def suggest(req: SuggestRequest):
    rows, index_available = search.search(
        req.product_description, lang=req.lang, kinds=("hs", "fraccion"), limit=5
    )
    warnings = ["Resultado informativo; la clasificación definitiva requiere validación especializada."]
    if not index_available:
        warnings.append("no confirmable: índice de clasificación no disponible; ejecuta importadores SNICE/VUCEM")

    tokens = [t for t in req.product_description.lower().split() if len(t) > 2][:6]
    candidates = [
        {
            "code": r["entity_id"],
            "level": r["kind"],
            "description": r["title"],
            "confidence": r["score"],
            "why": tokens,
        }
        for r in rows
    ]
    return ok({"candidates": candidates},
              trace=[{"source": "WCO", "label": "hs"}, {"source": "SNICE", "label": "nico_ligie"}],
              warnings=warnings)
