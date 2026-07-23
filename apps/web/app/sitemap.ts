// app/sitemap.ts — generates /sitemap.xml (report §SEO técnico).
//
// Emits the static routes plus one entry per country page, derived from the same
// built geometry that feeds the map (single source of truth). Each URL carries
// `alternates.languages` so Google sees the es/en pair (hreflang) without us
// maintaining a second list. Admin/ephemeral routes are never listed.
import type { MetadataRoute } from "next";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

function countryIso3s(): string[] {
  try {
    const p = join(process.cwd(), "public", "geo", "countries-50m.geojson");
    const fc = JSON.parse(readFileSync(p, "utf8")) as {
      features: { properties: { iso3: string | null } }[];
    };
    return fc.features
      .map((f) => f.properties.iso3)
      .filter((v): v is string => Boolean(v))
      .sort();
  } catch {
    // Geometry not built yet — the sitemap still lists the static routes.
    return [];
  }
}

function entry(path: string, priority: number): MetadataRoute.Sitemap[number] {
  return {
    url: `${BASE}${path}`,
    lastModified: new Date(),
    priority,
    alternates: {
      languages: {
        es: `${BASE}${path}`,
        en: `${BASE}${path}${path.includes("?") ? "&" : "?"}lang=en`,
      },
    },
  };
}

export default function sitemap(): MetadataRoute.Sitemap {
  const statics = [
    entry("/", 1),
    entry("/mapa", 0.9),
    entry("/arancel", 0.9),
    entry("/calculadora", 0.8),
  ];
  const countries = countryIso3s().map((iso3) => entry(`/pais/${iso3.toLowerCase()}`, 0.6));
  return [...statics, ...countries];
}
