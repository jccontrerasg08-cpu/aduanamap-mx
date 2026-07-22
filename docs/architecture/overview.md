# Arquitectura — visión general

## Capas

1. **Web pública** (`apps/web`) — Next.js. Mapa, país, tratado, fracción/NICO, calculadora. Bilingüe es/en.
2. **API de dominio** (`apps/api`) — FastAPI. Solo lectura pública. Envelope `data / source_trace / warnings`.
3. **Almacenamiento** — PostgreSQL + PostGIS (transaccional/geo) + Redis (caché). Object storage para snapshots crudos.
4. **Orquestación ETL** (`workers`) — jobs por fuente, cron. Reusa el core del repo `comercio-exterior-mexico`.

```
Usuario → CDN → Next.js → FastAPI → PostgreSQL/PostGIS + Redis + Object storage
                                    ↑
                              Workers ETL (cron) → Banxico · SNICE · VUCEM · ANAM · DOF · WCO/WITS · SRE
```

## Principios de datos

- **HS (6) universal / Fracción (8) + NICO (10) nacional.** Nunca mezclar niveles.
- **Versionar todo.** `hs_version`, `ligie_version`, `effective_from/to`. Un HS6 puede diferir entre HS2012/2017/2022.
- **Trazabilidad.** `source_manifest` (SHA-256, parser_version, status) + `source_document` (snapshot crudo).
- **Conteo según fuente.** SE (14 TLC / 52 países) vs ANAM (12 TLC / 46 países) no es error: es criterio. Se guarda en
  `agreement_source_claim` por afirmación, con fecha de consulta.

## Fallback por fuente (degradación elegante)

| Fuente | Orden |
|---|---|
| Banxico | API viva → snapshot Postgres → JSON en object storage → `stale` → "no disponible" |
| SNICE/VUCEM/ANAM | fuente viva → snapshot crudo previo → última tabla productiva → banner `stale` |
| DOF | publicación viva → PDF/HTML archivado → decreto previo relacionado → solo metadatos |
| WCO/WITS | recurso vivo → tabla de referencia local versionada → congelar y advertir |

## Frontera de la capa `ai/`

`ai/` **no calcula tasas, aranceles ni reglas de origen**. Solo:
- sugiere clasificación (con `confidence` + "por qué"), y
- busca en lenguaje natural sobre el corpus indexado.

La ruta tarifa/tasa/regla-de-origen son consultas deterministas contra tablas versionadas. Ver
[docs/decisions/0002-ai-boundary.md](../decisions/0002-ai-boundary.md).
