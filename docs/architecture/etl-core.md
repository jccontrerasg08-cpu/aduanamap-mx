# Núcleo ETL — reutilización de `comercio-exterior-mexico`

El repo [`jccontrerasg08-cpu/comercio-exterior-mexico`](https://github.com/jccontrerasg08-cpu/comercio-exterior-mexico)
ya implementa un ETL maduro y **poblado**. La estrategia del report se cumple al pie de la letra:
**no reescribir — encapsular sus jobs y migrar su warehouse curado a PostgreSQL.**

## Qué aporta el repo existente

- `src/comex/etl.py` — `run_etl(source)` descarga fuentes públicas con `User-Agent` propio, retries y
  TLS especial para VUCEM. Fuentes: `vucem-tigie`, `snice-nico`, `hs-global` (WITS), `vucem-notificaciones`,
  `vucem-hojas-informativas`, `anam-corpus`, `dof-comex`.
- `src/comex/manifest.py` — `Artifact(source_name, source_url, local_path, sha256, size_bytes, fetched_at)`.
  Mapea 1:1 a nuestro `source_manifest` + `source_document`.
- `src/comex/db.py` — warehouse DuckDB (`data/comex.duckdb`) con las tablas curadas que consume la API.
- CLI `comex.py` — `init-db`, `etl run [source]`, `etl status`, `warehouse-refresh`, RAG/DOF, forecast.

## Datos ya disponibles (snapshot verificado)

| Tabla DuckDB | Filas | Destino Postgres |
|---|---:|---|
| `tariff_fraction` | 16,225 | `mx_tariff_fraction` (7,859 con hs6) |
| `tariff_nico` / `dim_nico_catalog` | 6,294 | `mx_nico` |
| `catalog_item` (GLOBAL 2/4/6) | 22,841 | `hs_code` (8,358) |
| `vucem_tigie_items` | 14,483 | referencia clasificador |
| `anam_trade_agreements` | 20 | `agreement` + `agreement_source_claim` |
| `dof_publication` | 4 | DOF |
| `dim_banxico_series` / `fact_banxico_series_monthly` | 22 / 9,268 | `banxico_series` / `exchange_rate` |

## Cómo se conecta (workers)

```
workers/comex_bridge.py         # encapsula: invoca `python comex.py etl run …` en el repo existente
workers/migrate_duckdb_to_pg.py # migra: DuckDB (read-only) → Postgres, idempotente
```

Flujo operativo:

```bash
# 1) refrescar fuentes públicas usando el core existente (su venv, sus deps)
python -m workers.comex_bridge etl            # o: etl snice-nico
# 2) migrar el warehouse curado a la BD pública
python -m workers.migrate_duckdb_to_pg        # o: fractions | nicos | hs | agreements
```

`COMEX_REPO_PATH` (y opcional `COMEX_DUCKDB_PATH`) en `.env` apuntan al checkout.

## Frontera importante

DuckDB sigue siendo **staging + analítica local**; PostgreSQL/PostGIS sirve la **web pública y la API**.
No se duplica lógica de descarga: el core existente es la única fuente de captura; AduanaMap solo consume
su salida curada y le añade trazabilidad, versionado y API pública.
