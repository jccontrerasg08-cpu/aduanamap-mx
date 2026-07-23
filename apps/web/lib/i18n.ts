// lib/i18n.ts — lightweight bilingual (es/en) dictionary.
//
// The report requires es/en. Full hreflang locale routing is a later phase; for
// now `lang` is read from the `?lang=` search param (default "es") and passed
// both to this dictionary and to the API (which localizes names). Keeping the
// strings in one typed table makes adding English coverage a fill-in, not a
// refactor. `t(lang, key)` falls back to Spanish if a key lacks a translation.
export type Lang = "es" | "en";

export function normalizeLang(value: string | string[] | undefined): Lang {
  const v = Array.isArray(value) ? value[0] : value;
  return v === "en" ? "en" : "es";
}

type Dict = Record<string, { es: string; en: string }>;

const DICT: Dict = {
  tagline: {
    es: "Mundo → país → instrumento → código → cálculo → fuente.",
    en: "World → country → instrument → code → calculation → source.",
  },
  nav_map: { es: "Mapa mundial", en: "World map" },
  nav_tariff: { es: "Explorador arancelario", en: "Tariff explorer" },
  nav_calc: { es: "Calculadora", en: "Calculator" },
  api_status: { es: "Estado de la API", en: "API status" },
  unavailable: { es: "no disponible", en: "unavailable" },
  sources: { es: "Fuentes", en: "Sources" },
  warnings: { es: "Advertencias", en: "Warnings" },
  not_confirmable: { es: "No confirmable", en: "Not confirmable" },
  search: { es: "Buscar", en: "Search" },
  countries: { es: "Países", en: "Countries" },
  agreements: { es: "Instrumentos", en: "Agreements" },
  region: { es: "Región", en: "Region" },
  effective: { es: "Vigente desde", en: "Effective from" },
  members: { es: "Miembros", en: "Members" },
  estimate: { es: "Estimar", en: "Estimate" },
  customs_value: { es: "Valor en aduana (MXN)", en: "Customs value (MXN)" },
  disclaimer: {
    es: "Herramienta informativa y educativa. No constituye asesoría legal, fiscal ni aduanera. Cuando una preferencia o tasa no puede confirmarse con fuente estructurada, se marca como no confirmable.",
    en: "Informational and educational tool. Not legal, tax, or customs advice. When a preference or rate cannot be confirmed from a structured source, it is labeled not confirmable.",
  },
};

export function t(lang: Lang, key: keyof typeof DICT): string {
  const entry = DICT[key];
  if (!entry) return String(key);
  return entry[lang] || entry.es;
}
