# Cumplimiento del deep research report

Estado real y verificado del proyecto contra el informe. Se actualiza en cada iteración.
Leyenda: ✅ hecho y verificado · 🟡 parcial · ❌ pendiente · ⛔ bloqueado por entorno.

**Última verificación:** 2026-07-22 · 34 tests Python ✅ · `next build` ✅ · ruff ✅

## 1. Reglas no negociables (§Principios)

| Regla | Estado | Evidencia |
|---|---|---|
| No inventar tasas, reglas de origen ni preferencias | ✅ | `services/calculator.py` devuelve `not_confirmable` + duties `null`; test lo afirma |
| Versionar todo (`hs_version`, `ligie_version`, `effective_from/to`) | ✅ | migraciones 0001/0002 |
| Mostrar fecha efectiva + fuente primaria en cada pantalla | ✅ | `components/Trace.tsx` en todas las páginas |
| Degradar con elegancia | ✅ | API: envelope + warnings; Web: `lib/api.ts` nunca lanza |
| Separar público de operativo sensible | ✅ | no se piden credenciales VUCEM ni documentos |
| `ai/` nunca calcula tasas | ✅ | ADR 0002; `/api/classify/suggest` solo sugiere |

## 2. API pública (§Especificación base — 13 endpoints)

Los **13** endpoints del informe existen y devuelven el envelope `data/source_trace/warnings`:
`healthz`, `map/countries`, `countries/{iso3}`, `countries/{iso3}/agreements`, `agreements/{slug}`,
`tariff/search`, `tariff/{code}`, `classify/suggest`, `banxico/fix/latest`, `banxico/series/{id}/latest`,
`calculator/estimate`, `sources/status`, `wiki/{slug}` ✅ (+ `tariff/normalize/{code}` extra).

| Aspecto | Estado | Nota |
|---|---|---|
| Envelope en toda respuesta (incl. 429/500) | ✅ | handler global + middleware |
| Rate limit 429 + `Retry-After` | ✅ | `ratelimit.py`, límites por ruta del informe |
| Validación estricta de entrada | ✅ | Pydantic + regex por ruta |
| Caché con TTL por endpoint | 🟡 | Redis con TTL en Banxico; el resto usa `revalidate` en Next, no la tabla TTL completa del informe |
| OpenAPI/Swagger automático | ✅ | `/docs`, `/redoc` |

## 3. Datos y esquema (§Esquema lógico)

| Aspecto | Estado | Nota |
|---|---|---|
| Todas las tablas del informe | ✅ | 22 tablas (0001+0002); verificado que no falta ninguna |
| Integridad de FKs | ✅ | verificado: todas las `REFERENCES` resuelven |
| `agreement_source_claim` (SE 14/52 vs ANAM 12/46) | ✅ tabla / ❌ datos | el criterio "conteo según fuente" está modelado |
| Migraciones ejecutadas contra PostGIS | ⛔ | **Docker no disponible en este entorno**; nunca se han corrido |
| Datos reales cargados | ⛔ | depende de lo anterior; endpoints devuelven vacío + warning (correcto) |

## 4. ETL (§Pipeline y cron)

| Etapa | Estado | Nota |
|---|---|---|
| capture → preserve (SHA-256 + manifest) | ✅ | `workers/common/{http,manifest,source_job}.py` |
| Reintentos con backoff + UA identificable | ✅ | `http.py` |
| `etl_run` / `etl_error_log` | ✅ | ciclo de vida completo |
| Banxico FIX (fetch→snapshot→upsert) | ✅ | + fallback `stale` |
| `seed_countries` / `geometry_import` | ✅ | 236 países desde el GeoJSON construido |
| parse → normalize por fuente (SNICE/VUCEM/ANAM/DOF) | ❌ | requiere el **formato real** de cada fuente; no se inventa un parser a ciegas |
| Cron schedules del informe (`infra/`) | ❌ | tabla de horarios documentada, no implementada |
| Orden de fallback por fuente | ✅ doc / 🟡 código | documentado en `architecture/overview.md`; implementado en Banxico |

## 5. Frontend (§Pantallas troncales)

| Pantalla | Estado |
|---|---|
| Inicio | ✅ |
| Mapa mundial | ✅ lista accesible (primaria) + MapLibre choropleth (mejora progresiva, ADR 0004) |
| País / Tratado / Fracción-NICO | ✅ |
| Calculadora | ✅ |
| Fuentes (estatus ETL visible al público) | ❌ existe `/api/sources/status`, falta la página |
| Admin | ❌ (Fase P2 del informe) |

## 6. SEO y accesibilidad (§SEO y accesibilidad)

| Ítem | Estado |
|---|---|
| `sitemap.xml` | ✅ 240 URLs (4 estáticas + 236 países) |
| `robots.txt` | ✅ excluye `/admin`, `/api/`, resultados efímeros `?q=` |
| Canonical + `hreflang` es/en | ✅ `metadataBase` + `alternates.languages` (480 alternates en el sitemap) |
| Metadata por ruta | ✅ template de título + descripción |
| OG / Twitter card | 🟡 metadata sí; falta imagen OG generada por ruta |
| JSON-LD (rich results) | ❌ |
| Teclado, foco visible, skip-link, landmarks | ✅ |
| Alternativa accesible al mapa | ✅ la tabla es la ruta primaria; canvas `aria-hidden` |
| Contraste AA verificado | 🟡 tokens diseñados para AA, sin auditoría axe |
| Peso inicial controlado / lazy map | ✅ `/mapa` first-load **321 kB → 97.9 kB** (maplibre en chunk diferido) |

## 7. Seguridad (§Checklist)

| Control | Estado |
|---|---|
| Secrets solo por entorno | ✅ |
| CSP, HSTS, nosniff, frame-ancestors, Referrer/Permissions-Policy | ✅ ADR 0003 (HSTS solo prod) |
| Rate limiting 429 | ✅ |
| Validación de entrada | ✅ |
| PII minimizada (calculadora anónima) | ✅ |
| Logs sin secretos | ✅ logs JSON estructurados |
| `audit_log` admin/ETL/editorial | ❌ |
| Backups probados / escaneo SCA | ❌ |
| Auth admin + MFA | ❌ (no hay admin aún) |

## 8. Testing (§Plan de testing)

| Capa | Estado |
|---|---|
| Unit (normalización HS, utilidades) | ✅ |
| Contract (envelope en todos los endpoints) | ✅ 17 endpoints barridos |
| ETL parser | 🟡 tests de parseo y retry; faltan snapshots dorados |
| Failover (API/DB/Redis caídos) | ✅ toda la suite corre sin infraestructura |
| Integración DB (migraciones idempotentes) | ⛔ requiere Postgres |
| Search relevancia · UI Playwright · axe · Lighthouse · DAST | ❌ |

## 9. CI/CD y observabilidad

| Ítem | Estado |
|---|---|
| CI: lint + tests + build web real | ✅ `.github/workflows/ci.yml` |
| Docker Compose (db/redis/api/workers) | ✅ definido, sin ejecutar ⛔ |
| Publicar imágenes GHCR · preview deploy · migraciones en CD · rollback | ❌ |
| Logs estructurados | ✅ |
| OpenTelemetry · métricas · alertas de freshness · uptime | ❌ |

## Bloqueadores reales

1. **⛔ Docker/Postgres no disponible aquí** → migraciones y carga de datos nunca ejecutadas. Todo el
   código de datos está escrito y corre en DRY-RUN; falta el entorno para probarlo de verdad.
2. **❌ Parsers de fuentes** → necesitan un snapshot real del formato de SNICE/VUCEM/ANAM/DOF.
   Escribirlos a ciegas violaría la regla de no inventar.
