// Shared API response envelope — mirror of packages/schemas/python/envelope.py.
// Every API response is data + source_trace + warnings.

export interface SourceTrace {
  source: string; // "Banxico" | "SNICE" | "SRE" | "WCO/WITS" | ...
  label?: string;
  fetched_at?: string; // ISO-8601
}

export interface Envelope<T> {
  data: T | null;
  source_trace: SourceTrace[];
  warnings: string[];
}

export function isConfirmable<T>(env: Envelope<T>): boolean {
  return env.data !== null && !env.warnings.some((w) => w.startsWith("no confirmable"));
}
