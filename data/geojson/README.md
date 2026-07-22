# data/geojson

Geometrías de países para el mapa mundial (MapLibre). Cargar polígonos simplificados
(Natural Earth 1:110m o 1:50m) a `country_geometry.geom` (SRID 4326, MultiPolygon).

No versionar los archivos crudos grandes aquí: se importan vía worker y se guardan en
`country_geometry` con `source_name` + `source_hash` para trazabilidad.
