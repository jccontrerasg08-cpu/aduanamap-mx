// components/WorldMap.tsx — interactive world choropleth (progressive enhancement).
//
// Rendered BELOW the accessible country table in /mapa; the table remains the
// primary, WebGL-independent path (ADR 0004). This canvas adds visual richness
// for users who can use it.
//
// Design choices from the map research (ADR 0004):
//  - Self-contained style: an ocean background + our own country polygons. No
//    external tile server or API key is required, so the map works offline/now.
//    A richer basemap is opt-in via NEXT_PUBLIC_MAP_STYLE_URL (e.g. a PMTiles
//    style); when set, PMTiles' protocol is registered and that style is used.
//  - Choropleth color is DATA-DRIVEN (['get','buckets'] on a property merged into
//    the GeoJSON client-side), NOT feature-state — feature-state + fill-color has
//    a known bug (maplibre-gl-js#4930). feature-state is used only for hover.
//  - Coloring is by relationship with Mexico (agreements_count from the API). With
//    no data loaded every country is neutral — honest, never invented.
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import MapGL, { Source, Layer, type MapRef, type MapLayerMouseEvent } from "react-map-gl/maplibre";
import maplibre from "maplibre-gl";
import { Protocol } from "pmtiles";
import "maplibre-gl/dist/maplibre-gl.css";
import type { MapCountry } from "@/lib/api";

const GEO_URL = "/geo/countries-50m.geojson";
const STYLE_URL = process.env.NEXT_PUBLIC_MAP_STYLE_URL;

// Register the PMTiles protocol once (only relevant if a pmtiles:// style is used).
let pmtilesRegistered = false;
function ensurePmtiles() {
  if (pmtilesRegistered) return;
  maplibre.addProtocol("pmtiles", new Protocol().tile);
  pmtilesRegistered = true;
}

type FC = GeoJSON.FeatureCollection<GeoJSON.Geometry, Record<string, unknown>>;

// Ocean + neutral land palette; green ramp encodes number of instruments with MX.
const OCEAN = "#a9c9e0";
const NEUTRAL = "#e6e9ee";
const MX = "#1b6b3a";
const RAMP: [number, string][] = [
  [1, "#c7e9c0"],
  [2, "#74c476"],
  [3, "#31a354"],
];

const selfContainedBg: maplibre.LayerSpecification = {
  id: "bg",
  type: "background",
  paint: { "background-color": OCEAN },
};

// fill-color: Mexico distinct; else stepped by agreements_count; else neutral.
const fillPaint: maplibre.FillLayerSpecification["paint"] = {
  "fill-color": [
    "case",
    ["==", ["get", "iso3"], "MEX"],
    MX,
    ["step", ["coalesce", ["get", "agreements_count"], 0], NEUTRAL, ...RAMP.flatMap(([n, c]) => [n, c])],
  ],
  "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.95, 0.75],
};

const linePaint: maplibre.LineLayerSpecification["paint"] = {
  "line-color": "#ffffff",
  "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 1.4, 0.4],
};

export function WorldMap({ countries }: { countries: MapCountry[] }) {
  const router = useRouter();
  const mapRef = useRef<MapRef | null>(null);
  const hovered = useRef<string | number | null>(null);
  const [data, setData] = useState<FC | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Merge the API relationship data into the static geometry (data-driven color).
  const counts = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of countries) m.set(c.iso3, c.agreements_count);
    return m;
  }, [countries]);

  useEffect(() => {
    setReducedMotion(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false);
    let alive = true;
    fetch(GEO_URL)
      .then((r) => (r.ok ? r.json() : null))
      .then((fc: FC | null) => {
        if (!alive || !fc) return;
        for (const f of fc.features) {
          const iso3 = (f.properties?.iso3 as string) ?? null;
          f.properties = { ...f.properties, agreements_count: iso3 ? counts.get(iso3) ?? 0 : 0 };
        }
        setData(fc);
      })
      .catch(() => setData(null));
    return () => {
      alive = false;
    };
  }, [counts]);

  const setHover = useCallback((id: string | number | null) => {
    const map = mapRef.current;
    if (!map) return;
    if (hovered.current !== null) {
      map.setFeatureState({ source: "countries", id: hovered.current }, { hover: false });
    }
    if (id !== null) map.setFeatureState({ source: "countries", id }, { hover: true });
    hovered.current = id;
  }, []);

  const onMove = useCallback(
    (e: MapLayerMouseEvent) => {
      const f = e.features?.[0];
      const map = mapRef.current;
      if (map) map.getCanvas().style.cursor = f && f.id != null ? "pointer" : "";
      setHover(f && f.id != null ? f.id : null);
    },
    [setHover],
  );

  const onClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const iso3 = e.features?.[0]?.properties?.iso3 as string | undefined;
      if (iso3) router.push(`/pais/${iso3.toLowerCase()}`);
    },
    [router],
  );

  const mapStyle = useMemo(() => {
    if (STYLE_URL) {
      if (STYLE_URL.includes("pmtiles")) ensurePmtiles();
      return STYLE_URL;
    }
    // Minimal self-contained style: just the ocean background. Country layers are
    // added declaratively via <Source>/<Layer> below.
    return { version: 8 as const, sources: {}, layers: [selfContainedBg], glyphs: undefined };
  }, []);

  if (data === null) {
    return (
      <p className="card" role="status">
        Cargando mapa… (si no aparece, usa la lista de países de arriba).
      </p>
    );
  }

  return (
    <div
      style={{ height: 460, borderRadius: "var(--radius)", overflow: "hidden", border: "1px solid var(--border)" }}
      aria-hidden="true"
    >
      <MapGL
        ref={mapRef}
        initialViewState={{ longitude: -40, latitude: 20, zoom: 1.4 }}
        mapStyle={mapStyle}
        interactiveLayerIds={["country-fill"]}
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        onClick={onClick}
        dragRotate={false}
        // Respect reduced-motion: disable inertial/animated camera moves.
        {...(reducedMotion ? { fadeDuration: 0 } : {})}
      >
        <Source id="countries" type="geojson" data={data} promoteId="iso3">
          <Layer id="country-fill" type="fill" paint={fillPaint} />
          <Layer id="country-line" type="line" paint={linePaint} />
        </Source>
      </MapGL>
    </div>
  );
}
