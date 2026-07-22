# Contribuir

## Setup

```bash
cp .env.example .env
docker compose up -d db redis
psql "$DATABASE_URL" -f core/migrations/0001_init.sql
cd apps/api && pip install -e .[dev] && uvicorn app.main:app --reload
```

## Reglas de oro (no negociables)

1. **No inventar** tasas, reglas de origen, regulaciones ni equivalencias. Ante duda: `no confirmable` + fuente primaria.
2. **Versionar todo**: `hs_version`, `ligie_version`, `effective_from/to`.
3. Cada respuesta de API mantiene el envelope **`data / source_trace / warnings`**.
4. Todo ETL preserva el **snapshot crudo con SHA-256** antes de parsear.
5. `ai/` nunca calcula tasas (ver [ADR 0002](docs/decisions/0002-ai-boundary.md)).

## Antes de un PR

- `ruff check apps/api/app workers`
- `pytest tests/unit tests/api -q`
- Si tocas el esquema, añade una migración nueva en `core/migrations/NNNN_*.sql` (no edites las existentes).
- Un directorio nuevo se justifica solo cuando el código llega. Nada de carpetas vacías especulativas.

## Commits

Formato convencional (`feat:`, `fix:`, `docs:`, `chore:`). PRs pequeños y enfocados.
