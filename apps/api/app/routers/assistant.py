"""Asistente especializado en comercio exterior de México (capa IA estrecha).

Expone `ai.assistant`, que responde SOLO desde el catálogo canónico y devuelve la
fuente; nunca afirma tasas ni reglas de origen (ADR 0002). Funciona sin base de
datos y sin LLM, así que el endpoint es útil incluso con la infraestructura caída.

La capa `ai/` vive en la raíz del monorepo (no puede importar la lógica de la
calculadora, por diseño), por lo que se localiza dinámicamente: se prueban las
carpetas ancestro hasta encontrar la que contiene `ai/` (repo root en local,
`/app` en la imagen Docker).
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..envelope import ok


def _ensure_ai_importable() -> None:
    try:
        import ai  # noqa: F401
        return
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "ai" / "assistant.py").exists():
            sys.path.insert(0, str(parent))
            return


_ensure_ai_importable()

try:
    from ai import assistant as ai_assistant
except ImportError:  # pragma: no cover - the endpoint degrades instead of crashing
    ai_assistant = None  # type: ignore

router = APIRouter(tags=["asistente"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    lang: str = Field("es", max_length=2)


@router.post("/api/assistant/ask")
def ask(req: AskRequest):
    """Pregunta en lenguaje natural sobre los TLC de México; respuesta fundamentada."""
    if ai_assistant is None:
        return ok(None, warnings=["no disponible: capa de asistente no instalada"])
    res = ai_assistant.answer(req.question, lang=req.lang)
    return ok(
        {"answer": res["answer"], "grounded": res["grounded"], "detail": res["data"]},
        trace=res["source_trace"],
        warnings=res["warnings"],
    )
