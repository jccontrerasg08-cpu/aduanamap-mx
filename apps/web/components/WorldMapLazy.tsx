// components/WorldMapLazy.tsx — code-split loader for the interactive map.
//
// Optimization required by the report ("peso inicial controlado, lazy loading de
// mapa"): importing <WorldMap> statically pulls maplibre-gl (~220 kB) into the
// /mapa route's first-load JS. Loading it through next/dynamic with ssr:false
// moves maplibre into its own chunk fetched after hydration, so the page — whose
// PRIMARY content is the accessible country table — paints and becomes usable
// without waiting on the map. The placeholder keeps layout stable (no CLS).
"use client";

import dynamic from "next/dynamic";
import type { MapCountry } from "@/lib/api";

const WorldMap = dynamic(() => import("./WorldMap").then((m) => m.WorldMap), {
  ssr: false,
  loading: () => (
    <div
      className="card"
      role="status"
      aria-live="polite"
      style={{ height: 460, display: "grid", placeItems: "center" }}
    >
      Cargando mapa interactivo… (la lista de países de arriba ya está disponible)
    </div>
  ),
});

export function WorldMapLazy({ countries }: { countries: MapCountry[] }) {
  return <WorldMap countries={countries} />;
}
