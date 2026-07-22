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
- [ ] Importador SNICE (LIGIE / NICO)
- [ ] Importador VUCEM (clasificador TIGIE)
- [ ] Importador ANAM (tratados / guías)
- [ ] Watcher DOF (comercio exterior)
- [ ] `/api/tariff/search`, `/api/tariff/{code}`, `/api/agreements/{slug}`

## Fase 3 — Frontend público
- [ ] Landing bilingüe
- [ ] Mapa mundial (MapLibre) + fallback accesible (lista de países)
- [ ] Página de país / tratado / fracción-NICO
- [ ] Estimador de costo aterrizado (conservador, `not_confirmable` por defecto)

## Fase 4 — Endurecimiento
- [ ] Accesibilidad AA + SEO (sitemap, hreflang es/en)
- [ ] Observabilidad (OTel, freshness alerts)
- [ ] Seguridad (headers, rate limiting 429 + Retry-After, ASVS L2)
- [ ] Beta pública

## Reglas no negociables
1. No inventar tasas, reglas de origen, regulaciones ni equivalencias.
2. Versionar todo (HS version, ligie_version, effective_from/to).
3. Mostrar fecha efectiva + fuente primaria en cada pantalla.
4. Degradar con elegancia cuando una fuente falle.
5. La capa `ai/` nunca calcula tasas — solo sugiere clasificación y busca sobre el corpus indexado.
