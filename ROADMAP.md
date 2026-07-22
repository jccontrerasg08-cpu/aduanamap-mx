# Roadmap

Salida en 4 fases. El MVP **no** intenta cobertura legal total desde el día 1.

## Fase 1 — Fundaciones (en curso)
- [x] Monorepo `apps/web`, `apps/api`, `workers`, `packages/schemas`, `core`
- [x] Migraciones base + trazabilidad (`source_manifest`, `source_document`, `etl_run`, `etl_error_log`)
- [x] Envelope `data / source_trace / warnings`
- [x] `/api/healthz`, `/api/sources/status`, `/api/banxico/fix/latest`
- [x] Worker Banxico FIX con snapshot + fallback `stale`
- [ ] CI (lint + test + typecheck)

## Fase 2 — API y datos
- [x] Encapsular núcleo ETL existente (`workers/comex_bridge.py`) — SNICE/VUCEM/ANAM/DOF/HS ya implementados en `comercio-exterior-mexico`
- [x] Migrador DuckDB→Postgres (`workers/migrate_duckdb_to_pg.py`) — 22,531 filas curadas listas (dry-run verificado)
- [ ] Ejecutar migración real contra Postgres (levantar `docker compose up -d db`)
- [x] `/api/tariff/normalize/{code}` (desglose determinista HS→Fracción→NICO)
- [x] `/api/tariff/{code}` (lookup versionado con `no confirmable` cuando falta catálogo)
- [x] `/api/tariff/search` (full-text tsvector), `/api/agreements/{slug}`
- [x] `/api/map/countries`, `/api/countries/{iso3}`, `/api/countries/{iso3}/agreements`
- [x] `/api/classify/suggest` (capa IA estrecha: solo sugerencia), `/api/wiki/{slug}`
- [x] `/api/banxico/series/{id}/latest`, `/api/calculator/estimate` (valor en aduana determinista)
- [x] Migración 0002 (tariff_rate, authority, rule_of_origin, wiki_page, search_index, calculator_case…)
- [x] Workers con capture robusto (retry/backoff + etl_run/etl_error_log): snice, vucem, anam, dof
- [ ] Escribir parsers de normalización por fuente (requiere snapshot real de cada formato)

## Fase 3 — Frontend público
- [ ] Landing bilingüe
- [ ] Mapa mundial (MapLibre) + fallback accesible (lista de países)
- [ ] Página de país / tratado / fracción-NICO
- [ ] Estimador de costo aterrizado (conservador, `not_confirmable` por defecto)

## Fase 4 — Endurecimiento
- [ ] Accesibilidad AA + SEO (sitemap, hreflang es/en)
- [ ] Observabilidad (OTel, freshness alerts)
- [x] Seguridad base: rate limiting 429 + Retry-After, validación Pydantic, CORS por entorno, logs sin secretos
- [ ] Headers CSP/HSTS, escaneo SCA, ASVS L2 completo
- [ ] Beta pública

## Reglas no negociables
1. No inventar tasas, reglas de origen, regulaciones ni equivalencias.
2. Versionar todo (HS version, ligie_version, effective_from/to).
3. Mostrar fecha efectiva + fuente primaria en cada pantalla.
4. Degradar con elegancia cuando una fuente falle.
5. La capa `ai/` nunca calcula tasas — solo sugiere clasificación y busca sobre el corpus indexado.
