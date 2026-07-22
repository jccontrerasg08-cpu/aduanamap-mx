"""Estimador de costo aterrizado. Valida entrada con Pydantic; nunca inventa tasas."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..config import get_settings
from ..envelope import ok
from ..services import calculator

router = APIRouter(tags=["calculadora"])


class EstimateRequest(BaseModel):
    country_origin: Optional[str] = Field(None, max_length=3)
    country_export: Optional[str] = Field(None, max_length=3)
    currency: str = Field("USD", max_length=3)
    invoice_value: float = Field(..., ge=0)
    freight: float = Field(0, ge=0)
    insurance: float = Field(0, ge=0)
    incoterm: str = Field("CIF", max_length=8)
    input_code: str = Field(..., max_length=16)
    agreement_slug: Optional[str] = Field(None, max_length=80)


@router.post("/api/calculator/estimate")
def estimate(req: EstimateRequest):
    settings = get_settings()
    data, trace, warnings = calculator.estimate(req.model_dump(), fix_serie=settings.banxico_fix_serie)
    return ok(data, trace=trace, warnings=warnings)
