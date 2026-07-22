"""AduanaMap MX public read API.

FastAPI gives automatic OpenAPI/Swagger at /docs and ReDoc at /redoc.
Every response follows the data / source_trace / warnings envelope.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import banxico, health, sources, tariff

app = FastAPI(
    title="AduanaMap MX API",
    version="0.1.0",
    description=(
        "API pública de referencia en comercio exterior de México. "
        "Cada respuesta incluye data, source_trace y warnings. "
        "No constituye asesoría legal, fiscal ni aduanera."
    ),
)

# Público de solo-lectura; en producción restringir origins vía APP_BASE_URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sources.router)
app.include_router(banxico.router)
app.include_router(tariff.router)


@app.get("/", tags=["ops"])
def root():
    return {
        "name": "AduanaMap MX API",
        "docs": "/docs",
        "endpoints": ["/api/healthz", "/api/sources/status", "/api/banxico/fix/latest",
                      "/api/tariff/normalize/{code}", "/api/tariff/{code}"],
        "disclaimer": "Herramienta informativa. No sustituye asesoría legal ni pedimento.",
    }
