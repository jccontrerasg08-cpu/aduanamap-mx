"""Explorador arancelario — HS / Fracción / NICO.

Ruta determinista: nunca inventa descripciones, tasas ni preferencias. Cuando un
nivel no existe en el catálogo versionado, la respuesta lo marca `no confirmable`
y muestra la fuente primaria para validación humana (ADR 0002).
"""
from __future__ import annotations

from fastapi import APIRouter

from ..envelope import ok
from ..services import tariff

router = APIRouter(tags=["arancel"])


@router.get("/api/tariff/normalize/{code}")
def normalize(code: str):
    """Desglose determinista de un código en HS2/HS4/HS6/Fracción8/NICO10.

    Puramente aritmético (no toca la base): útil incluso sin catálogo cargado.
    """
    return ok(tariff.normalize_code(code),
              trace=[{"source": "OMA/HS", "label": "regla_estructural"}])


@router.get("/api/tariff/{code}")
def resolve(code: str):
    """Resuelve un código contra las tablas versionadas (hs_code/fracción/NICO)."""
    data, trace, warnings = tariff.lookup(code)
    return ok(data, trace=trace, warnings=warnings)
