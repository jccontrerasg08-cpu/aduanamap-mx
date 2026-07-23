# ADR 0004 — Mapa mundial interactivo (MapLibre) y datos por país

- **Estado:** propuesto (planeación; aún no se escribe código de mapa)
- **Fecha:** 2026-07-22
- **Contexto de sesión:** el mapa es "una parte muy delicada". Esta ADR es el
  resultado de investigar múltiples repos de GitHub antes de escribir, siguiendo
  las reglas del proyecto (nunca inventar, versionar, trazar fuente, degradar,
  accesible). La capa accesible (lista de países en `/mapa`) **ya existe** y es la
  ruta primaria; el mapa WebGL se suma como **mejora progresiva** sobre los mismos
  datos de `/api/map/countries`.

## El punto más delicado: la clave de unión país ↔ geometría (`ISO_A3 = -99`)

Natural Earth deja `ISO_A3 = "-99"` para varios países soberanos (Francia, Noruega,
Kosovo, y otros). Si unimos la geometría con nuestra tabla `country` por `ISO_A3`
crudo, **esos países desaparecen silenciosamente del mapa** — un error de datos
grave y difícil de notar.

**Decisión:** al importar geometría, unir por `ISO_A3_EH` (extended harmonized) con
respaldo a `ADM0_A3`; nunca por `ISO_A3` crudo. Toda feature sin país correspondiente
se registra en `etl_error_log` (no se descarta en silencio). Se valida que el número
de geometrías cargadas == países esperados antes de publicar.

Fuentes del hallazgo:
[nvkelso/natural-earth-vector#131](https://github.com/nvkelso/natural-earth-vector/issues/131) ·
[#947](https://github.com/nvkelso/natural-earth-vector/issues/947) ·
[ropensci/rnaturalearth#77](https://github.com/ropensci/rnaturalearth/issues/77) ·
[geopandas#1041](https://github.com/geopandas/geopandas/issues/1041)

## Repositorios y fuentes elegidos (investigados)

| Necesidad | Elección | Alternativas evaluadas | Por qué |
|---|---|---|---|
| Geometría de países (mapa) | [topojson/world-atlas](https://github.com/topojson/world-atlas) (Natural Earth 110m/50m, dominio público) | [datasets/geo-countries](https://github.com/datasets/geo-countries), [georgique/world-geojson](https://github.com/georgique/world-geojson), [martynafford/natural-earth-geojson](https://github.com/martynafford/natural-earth-geojson), [LonnyGomes/CountryGeoJSONCollection](https://github.com/LonnyGomes/CountryGeoJSONCollection) | TopoJSON compacto, topología compartida (fronteras sin huecos), escalas 110m para overview / 50m para zoom |
| Datos de país (ISO2/3, nombre es/en, región) | [mledoze/countries](https://github.com/mledoze/countries) | [lukes/ISO-3166-Countries-with-Regional-Codes](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes), [planetopendata/awesome-world](https://github.com/planetopendata/awesome-world) | Trae traducciones (es/en), ISO 3166-1, región/subregión, flag SVG, y `independent` — cubre `country.name_es/name_en/region` |
| Basemap sin lock-in | [protomaps/basemaps](https://github.com/protomaps/basemaps) (PMTiles, un solo archivo estático + `addProtocol`) | OpenMapTiles, MapTiler (SaaS), demotiles (solo dev) | Un `.pmtiles` en object storage; sin servidor de tiles ni API key; alinea con "free-first" |
| Render en React | [visgl/react-maplibre](https://github.com/visgl/react-maplibre) | [richard-unterberg/maplibre-nextjs-ts-starter](https://github.com/richard-unterberg/maplibre-nextjs-ts-starter), maplibre-gl directo | Componente controlado + hooks; `ChoroplethOverlay` se movió a ejemplos → se implementa con `Source`/`Layer` |
| Simplificar geometría | [mbloch/mapshaper](https://github.com/mbloch/mapshaper) (CLI) | topojson-simplify | Visvalingam (no Douglas-Peucker: evita "spikes" en polígonos) + quantización |
| A11y de mapas | patrón [mapbox/mapbox-gl-accessibility](https://github.com/mapbox/mapbox-gl-accessibility) + [maplibre-gl-js#53](https://github.com/maplibre/maplibre-gl-js/issues/53) | — | Confirma: WCAG en el canvas es incompleto ⇒ la **lista accesible sigue siendo la ruta primaria** |
| Curaduría | [maplibre/awesome-maplibre](https://github.com/maplibre/awesome-maplibre) | — | Referencia viva de plugins/ejemplos |

## Arquitectura propuesta (flujo de datos)

```
mledoze/countries ─┐
                   ├─▶ worker seed_countries  ─▶ country (iso2/iso3/name_es/name_en/region)
world-atlas (NE) ──┘        │
                            └─▶ worker geometry_import (mapshaper simplify + join ISO_A3_EH)
                                        ─▶ country_geometry (geom 4326, source_name, source_hash)
                                                │
API  /api/map/countries (ya existe: lista + agreements_count)   ← ruta accesible
API  /api/map/geometry   (nuevo: FeatureCollection GeoJSON con iso3 + relación con MX)
                                                │
Web  /mapa : (1) tabla accesible [primaria]  +  (2) <MapLibre> choropleth [mejora progresiva]
```

Decisiones clave:
1. **Pre-join en ETL**, no en el cliente: la geometría se guarda ya ligada a `country.id`
   con `source_name` + `source_hash` (trazabilidad, igual que toda fuente).
2. **Choropleth por relación con México** (TLC / APPRI / ALADI / ninguno). Por el quirk
   de `fill-color` + `feature-state`
   ([maplibre-gl-js#4930](https://github.com/maplibre/maplibre-gl-js/issues/4930)),
   el color base se resuelve con una **propiedad data-driven en el GeoJSON**; el
   `feature-state` se reserva para hover/selección.
3. **Basemap configurable** vía `NEXT_PUBLIC_MAP_STYLE_URL` (ya en `.env.example`):
   demotiles en dev, PMTiles propio en prod.
4. **Fronteras = Natural Earth**, fuente cartográfica neutral. Se añade nota: los
   límites siguen a Natural Earth y no constituyen una postura política (coherente con
   el disclaimer y con "mostrar fuente").

## Plan de implementación (fases, cuando se escriba)

1. `workers/seed_countries.py` — cargar `country` desde mledoze/countries (es/en + ISO).
2. `workers/geometry_import.py` — descargar world-atlas, `mapshaper -simplify visvalingam`,
   unir por `ISO_A3_EH`/`ADM0_A3`, upsert `country_geometry`, registrar manifest + errores.
3. API `/api/map/geometry?lang=` — FeatureCollection (props: `iso3`, `name`, `relationship`,
   `agreements_count`), con envelope/trazabilidad y caché 24 h.
4. Web: componente cliente `<WorldMap>` (react-maplibre) montado **debajo** de la tabla
   accesible en `/mapa`; `Source` GeoJSON + `Layer` fill choropleth + hover por `feature-state`;
   panel lateral al seleccionar país → enlaza a `/pais/[iso3]`.
5. A11y: la tabla es la ruta primaria; el canvas añade `role`/aria, respeta `prefers-reduced-motion`,
   navegación por teclado; nunca es la única vía.

## Consecuencias

- (+) El mapa se construye sobre datos ya trazados y versionados; sin API keys ni lock-in.
- (+) El gotcha `-99` se ataja en el ETL con validación, no se descubre en producción.
- (+) Accesibilidad garantizada por diseño (lista primaria + mapa opcional).
- (−) `geometry_import` depende de `mapshaper` (Node) en el pipeline de workers (Python);
  se ejecuta como paso de build de datos, no en cada request.
- (−) PMTiles propio requiere generar/hostear un `.pmtiles` (diferible; demotiles cubre el MVP).

## Fuentes

Investigación registrada en [docs/references.md](../references.md) y en la memoria
del proyecto (codebase-memory ADR + memoria de archivos).
