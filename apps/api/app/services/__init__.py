"""Service layer: query + business logic behind the routers.

Deterministic and traceable by design — services read versioned tables and never
fabricate a rate, rule of origin, or preference. Members:
- `tariff`     — HS→Fracción→NICO normalization + versioned lookup
- `calculator` — landed-cost estimate (deterministic customs value; duties never invented)
- `search`     — full-text search over the indexed corpus (Postgres tsvector)
"""
