"""AduanaMap MX API package.

FastAPI application exposing the public read API. Every response follows the
data/source_trace/warnings envelope. Modules:
- `main`       — app assembly + middleware (CORS, rate limit, security headers) + error handler
- `config`     — environment-driven settings + startup validation
- `envelope`   — response contract + ok()/not_confirmable()/error() helpers
- `db`/`cache` — Postgres/Redis access that degrades to None when unavailable
- `ratelimit`  — fixed-window 429 + Retry-After limiter
- `logging`    — structured JSON logs
- `routers/`   — HTTP endpoints; `services/` — query + business logic
"""
