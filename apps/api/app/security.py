"""Security response headers middleware.

Adapted from the defensive-security playbook in the knowledge vault
(Wiki/Security & Cybersecurity → "Security Headers") and OWASP's guidance
(https://owasp.org/www-project-top-ten/, https://owasp.org/www-project-secure-headers/).

Adds the standard hardening headers to every response — the cheapest win in web
security. Two deliberate accommodations keep the API usable:

  - HSTS is only sent in production. On localhost over http it is pointless and
    would wrongly pin the browser to https.
  - The CSP allows the jsDelivr CDN that FastAPI's Swagger UI (/docs) loads from,
    so interactive docs keep working. JSON API responses aren't executed by the
    browser, so CSP mainly protects the docs page here.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

# Swagger UI (/docs) and ReDoc pull assets from jsDelivr; allow just that origin.
_SWAGGER_CDN = "https://cdn.jsdelivr.net"

_CSP = (
    "default-src 'self'; "
    f"script-src 'self' {_SWAGGER_CDN} 'unsafe-inline'; "
    f"style-src 'self' {_SWAGGER_CDN} 'unsafe-inline'; "
    f"img-src 'self' data: {_SWAGGER_CDN} https://fastapi.tiangolo.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

_STATIC_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": _CSP,
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardening headers to every response; never blocks the request."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for key, value in _STATIC_HEADERS.items():
            response.headers.setdefault(key, value)
        # HSTS only makes sense over real HTTPS in production.
        if get_settings().is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response
