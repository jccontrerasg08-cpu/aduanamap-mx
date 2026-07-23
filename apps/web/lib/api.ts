// lib/api.ts — typed, fail-safe client for the AduanaMap MX API.
//
// Every call returns the data/source_trace/warnings Envelope (shared contract in
// packages/schemas/ts/envelope.ts). The client NEVER throws: on a network error,
// non-2xx, or bad JSON it returns an Envelope with data:null and a warning, so
// server components render a graceful "no disponible" state instead of crashing.
// This mirrors the API's own degradation discipline on the frontend.
import type { Envelope } from "@schemas/envelope";

const BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

// Read endpoints are safe to cache briefly; callers can override.
const DEFAULT_REVALIDATE = 300;

function offline<T>(reason: string): Envelope<T> {
  return { data: null, source_trace: [], warnings: [`no disponible: ${reason}`] };
}

async function request<T>(
  path: string,
  init?: RequestInit & { revalidate?: number },
): Promise<Envelope<T>> {
  const url = `${BASE}${path}`;
  try {
    const res = await fetch(url, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
      next: { revalidate: init?.revalidate ?? DEFAULT_REVALIDATE },
    });
    if (!res.ok) {
      // 4xx/5xx still often carry an envelope; try to surface it.
      const body = await res.json().catch(() => null);
      if (body && typeof body === "object" && "warnings" in body) {
        return body as Envelope<T>;
      }
      return offline<T>(`API respondió ${res.status}`);
    }
    return (await res.json()) as Envelope<T>;
  } catch {
    return offline<T>("no se pudo contactar la API");
  }
}

export function apiGet<T>(path: string, revalidate?: number): Promise<Envelope<T>> {
  return request<T>(path, { method: "GET", revalidate });
}

export function apiPost<T>(path: string, body: unknown): Promise<Envelope<T>> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    revalidate: 0,
  });
}

// ── Typed shapes for the endpoints the web app consumes ─────────────────────
export interface HealthDoc {
  status: string;
  version: string;
  dependencies?: Record<string, string>;
}
export interface MapCountry {
  iso3: string;
  name: string;
  layer: string;
  agreements_count: number;
}
export interface CountryProfile {
  iso2: string;
  iso3: string;
  name: string;
  region: string | null;
  subregion: string | null;
  has_preferential_agreement: boolean;
  agreements: string[];
  country_page_slug: string;
}
export interface AgreementRow {
  slug: string;
  name: string;
  type: string | null;
  status: string | null;
  effective_date: string | null;
}
export interface AgreementDetail extends AgreementRow {
  members: string[];
  signed_date: string | null;
  documents: { title: string; kind: string; document_id: string }[];
}
export interface TariffNormalize {
  input: string;
  digits: string;
  hs2?: string;
  hs4?: string;
  hs6?: string;
  fraccion8?: string;
  nico10?: string;
}
export interface TariffDetail {
  normalize: TariffNormalize;
  hs6: { hs_version: string; description_es: string; description_en: string | null } | null;
  fraccion: { ligie_version: string; description_es: string; unit: string | null } | null;
  nico: { description_es: string } | null;
}
export interface TariffSearchRow {
  display_code: string;
  level: string;
  description: string;
  score: number;
}
export interface FixLatest {
  series_id: string;
  label?: string;
  date?: string;
  value?: number;
  status?: string;
}
export interface EstimateResult {
  mxn_exchange_rate: number | null;
  customs_value_mxn: number | null;
  estimated_igi_mxn: number | null;
  estimated_dta_mxn: number | null;
  estimated_iva_mxn: number | null;
  preferential_treatment: string;
  explanation: string;
}
