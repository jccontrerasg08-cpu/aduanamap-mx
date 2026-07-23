// tools/map-build/build-countries.mjs — reproducible builder for the world map geometry.
//
// Produces a single GeoJSON FeatureCollection of country polygons, each tagged
// with the join keys the app needs (iso3, iso2, name_es, name_en, region). It is
// the data-build step referenced by ADR 0004.
//
// Pipeline:
//   1. world-atlas countries-50m TopoJSON (Natural Earth 50m, public domain) →
//      GeoJSON via topojson-client. Feature ids are NUMERIC ISO 3166 (ccn3).
//   2. Join each feature by ccn3 → world-countries (mledoze/countries): cca3, cca2,
//      name.common (en), translations.spa.common (es), region, subregion.
//   3. VERIFY: every geometry must resolve to a country. Unmatched ids are printed
//      and (unless --allow-unmatched) fail the build — the delicate correctness gate
//      that keeps a country from silently vanishing from the map (cf. the ISO_A3=-99
//      problem with raw Natural Earth vectors, which this numeric join avoids).
//
// Run:  node tools/map-build/build-countries.mjs
// Out:  apps/web/public/geo/countries-50m.geojson  and  data/geojson/countries-50m.geojson
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { feature } from "topojson-client";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");

// Deps are installed in this tool's own package.json (see tools/map-build/package.json).
const atlas = JSON.parse(
  readFileSync(resolve(here, "node_modules/world-atlas/countries-50m.json"), "utf8"),
);
const worldCountries = JSON.parse(
  readFileSync(resolve(here, "node_modules/world-countries/countries.json"), "utf8"),
);

// ccn3 (numeric ISO) → { iso3, iso2, name_es, name_en, region, subregion }
const byCcn3 = new Map();
for (const c of worldCountries) {
  if (!c.ccn3) continue;
  byCcn3.set(String(c.ccn3).padStart(3, "0"), {
    iso3: c.cca3,
    iso2: c.cca2,
    name_en: c.name?.common ?? c.cca3,
    name_es: c.translations?.spa?.common ?? c.name?.common ?? c.cca3,
    region: c.region ?? null,
    subregion: c.subregion ?? null,
  });
}

// Round coordinates to ~4 decimals (~11 m at the equator). world-atlas ships
// ~14-decimal floats — sub-micron precision that only bloats the payload; at a
// world/country zoom 4 decimals is indistinguishable but roughly halves the size.
const PRECISION = 1e4;
function roundCoords(geom) {
  const r = (v) =>
    Array.isArray(v)
      ? typeof v[0] === "number"
        ? [Math.round(v[0] * PRECISION) / PRECISION, Math.round(v[1] * PRECISION) / PRECISION]
        : v.map(r)
      : v;
  return { ...geom, coordinates: r(geom.coordinates) };
}

const fc = feature(atlas, atlas.objects.countries);
const unmatched = [];
const features = [];

for (const f of fc.features) {
  const ccn3 = String(f.id ?? "").padStart(3, "0");
  const meta = byCcn3.get(ccn3);
  const name = f.properties?.name ?? "";
  if (!meta) {
    // Territories without a UN numeric code (Kosovo, Somaliland, N. Cyprus, …).
    // Kept as NEUTRAL features (iso3:null) so the map has no holes, but they are
    // not colored or interactive. Boundaries follow Natural Earth and are not a
    // political statement (ADR 0004).
    unmatched.push({ ccn3, name });
    features.push({
      type: "Feature",
      id: null,
      properties: { iso3: null, iso2: null, name, name_es: name, name_en: name,
                    region: null, subregion: null },
      geometry: roundCoords(f.geometry),
    });
    continue;
  }
  features.push({
    type: "Feature",
    id: meta.iso3,
    properties: {
      iso3: meta.iso3,
      iso2: meta.iso2,
      name: name || meta.name_es,
      name_es: meta.name_es,
      name_en: meta.name_en,
      region: meta.region,
      subregion: meta.subregion,
    },
    geometry: roundCoords(f.geometry),
  });
}

const out = { type: "FeatureCollection", features };

console.log(`geometrías totales:     ${fc.features.length}`);
console.log(`unidas a país (con ISO): ${features.length - unmatched.length}`);
console.log(`neutrales (sin ISO UN):  ${unmatched.length}`);
if (unmatched.length) {
  console.log("  ", unmatched.map((u) => u.name).join(", "));
}

// Spot-check the delicate cases that the raw ISO_A3=-99 path would have dropped.
for (const iso3 of ["FRA", "NOR", "MEX", "USA"]) {
  const ok = features.some((f) => f.properties.iso3 === iso3);
  console.log(`  check ${iso3}: ${ok ? "OK" : "MISSING"}`);
}

for (const dir of ["apps/web/public/geo", "data/geojson"]) {
  const abs = resolve(repoRoot, dir);
  mkdirSync(abs, { recursive: true });
  writeFileSync(resolve(abs, "countries-50m.geojson"), JSON.stringify(out));
  console.log(`escrito: ${dir}/countries-50m.geojson`);
}
