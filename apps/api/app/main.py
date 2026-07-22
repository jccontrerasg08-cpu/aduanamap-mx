"""AduanaMap MX public read API.

FastAPI gives automatic OpenAPI/Swagger at /docs and ReDoc at /redoc.
Every response follows the data / source_trace / warnings envelope.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from . import envelope, ratelimit
from .config import get_settings
from .logging import get_logger
from .routers import agreements, banxico, calculator, classify, countries, health, sources, tariff, wiki

log = get_logger("api")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    for w in settings.startup_warnings():
        log.warning("startup", extra={"extra": {"warning": w}})
    yield


app = FastAPI(
    title="AduanaMap MX API",
    version=settings.version,
    description=(
        "API pública de referencia en comercio exterior de México. "
        "Cada respuesta incluye data, source_trace y warnings. "
        "No constituye asesoría legal, fiscal ni aduanera."
    ),
    lifespan=lifespan,
)


# ── CORS (restringido por APP_BASE_URL en producción) ───────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Rate limiting → 429 + Retry-After ───────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or not request.url.path.startswith("/api/"):
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        decision = ratelimit.check(client, request.url.path)
        if not decision.allowed:
            log.info("rate_limited", extra={"extra": {"client": client, "path": request.url.path}})
            resp = JSONResponse(
                status_code=429,
                content=envelope.error("Rate limit excedido. Reintenta más tarde."),
            )
            resp.headers["Retry-After"] = str(decision.retry_after)
            resp.headers["X-RateLimit-Limit"] = str(decision.limit)
            resp.headers["X-RateLimit-Remaining"] = "0"
            return resp
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        return response


app.add_middleware(RateLimitMiddleware)


# ── Fallback: unhandled errors still return the envelope shape ───────────────
@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.error("unhandled", extra={"extra": {"path": request.url.path}}, exc_info=exc)
    return JSONResponse(status_code=500, content=envelope.error("Error interno; el equipo fue notificado."))


for r in (health, sources, banxico, tariff, countries, agreements, calculator, classify, wiki):
    app.include_router(r.router)


@app.get("/", tags=["ops"])
def root():
    return {
        "name": "AduanaMap MX API",
        "docs": "/docs",
        "endpoints": [
            "/api/healthz", "/api/sources/status",
            "/api/map/countries", "/api/countries/{iso3}", "/api/countries/{iso3}/agreements",
            "/api/agreements/{slug}",
            "/api/tariff/normalize/{code}", "/api/tariff/{code}", "/api/tariff/search",
            "/api/classify/suggest",
            "/api/banxico/fix/latest", "/api/banxico/series/{id}/latest",
            "/api/calculator/estimate",
            "/api/wiki/{slug}",
        ],
        "disclaimer": "Herramienta informativa. No sustituye asesoría legal ni pedimento.",
    }
