# AduanaMap MX / TradeWiki MX

Plataforma pública, bilingüe y *free-first* de referencia en comercio exterior de México:
**mapa mundial interactivo + wiki jurídica-operativa + explorador arancelario (HS / Fracción / NICO) +
guía de autoridades + estimador de costo aterrizado**, todo con **trazabilidad de fuentes oficiales**.

> Herramienta informativa y educativa. **No** constituye asesoría legal, fiscal, aduanera ni arancelaria.
> Cuando una preferencia o tasa no puede confirmarse con fuente estructurada, el sistema la marca
> explícitamente como **`no confirmable`** y muestra la fuente primaria para validación humana.

## Principio rector

**Lo universal es HS (OMA, 6 dígitos); lo nacional es TIGIE/NICO (Fracción 8 + NICO → 10 dígitos).**
Cada respuesta de la API es una combinación de **`data` + `source_trace` + `warnings`**. Nunca se inventan
tasas, reglas de origen ni preferencias.

## Arquitectura (day-1, deliberadamente lean)

Tres procesos, no microservicios: **`web`**, **`api`**, **`workers`**. La estructura crece cuando el código
llega, no antes.

```
aduanamap-mx/
├── apps/
│   ├── web/          # Next.js (mapa, país, tratado, código, calculadora)  [stub]
│   └── api/          # FastAPI — envelope data/source_trace/warnings
├── workers/          # ETL: capture → preserve → parse → normalize → publish
├── packages/schemas/ # Contratos compartidos (envelope) TS + Python
├── core/
│   └── migrations/   # SQL versionado (source_manifest, hs_code, fracción, nico…)
├── data/{raw,snapshots,processed,geojson}/   # raw snapshot discipline (SHA-256)
├── ai/               # UN agente + tools + prompts (narrow; nunca calcula tasas)
├── infra/            # docker/, github-actions/  (sin k8s/terraform todavía)
├── tests/{unit,api,etl}/
└── docs/{architecture,decisions}/
```

Ver [docs/architecture/overview.md](docs/architecture/overview.md),
[docs/decisions/0001-lean-scaffold.md](docs/decisions/0001-lean-scaffold.md) y
[docs/references.md](docs/references.md) (buenas prácticas aplicadas y su fuente).

## Quick start

```bash
cp .env.example .env          # completa BANXICO_TOKEN (64 chars) si tienes uno
docker compose up -d db redis # Postgres+PostGIS y Redis
docker compose up api         # FastAPI en http://localhost:8000  (/docs para OpenAPI)
```

Sin Docker (solo API):

```bash
cd apps/api
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -e .
uvicorn app.main:app --reload
```

Aplicar migraciones:

```bash
psql "$DATABASE_URL" -f core/migrations/0001_init.sql
```

## Estado del MVP (Fase 1)

- [x] Scaffold del monorepo (web / api / workers / core / packages)
- [x] Migración inicial: `source_manifest`, `source_document`, `country`, `hs_code`,
      `mx_tariff_fraction`, `mx_nico`, `etl_run`, `etl_error_log`
- [x] API: envelope compartido + `/api/healthz` + `/api/sources/status` + `/api/banxico/fix/latest`
- [x] Worker Banxico FIX (con snapshot crudo + manifest + fallback `stale`)
- [x] Núcleo ETL: encapsulado desde `comercio-exterior-mexico` (`workers/comex_bridge.py`) +
      migrador DuckDB→Postgres (`workers/migrate_duckdb_to_pg.py`) — ver [docs/architecture/etl-core.md](docs/architecture/etl-core.md)
- [ ] Ejecutar migración real (22,531 filas curadas ya disponibles: 7,859 fracciones, 6,294 NICOs, 8,358 HS, 20 tratados)
- [ ] Frontend: mapa mundial + página de país
- [ ] Estimador de costo aterrizado

Ver [ROADMAP.md](ROADMAP.md).

## Licencia

MIT — ver [LICENSE](LICENSE).
