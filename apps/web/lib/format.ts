// lib/format.ts — small, dependency-free formatting helpers.
//
// Kept pure so they work in Server Components without pulling in a locale lib.
// Money uses MXN grouping; codes are shown with the conventional dotted grouping
// (HS6 → 7318.15, fracción → 7318.15.99, NICO → 7318.15.99.00).

export function money(value: number | null | undefined, currency = "MXN"): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

export function num(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-MX").format(value);
}

/** Group a numeric HS/fracción/NICO code into dotted pairs for display. */
export function prettyCode(code: string | null | undefined): string {
  if (!code) return "—";
  const d = code.replace(/\D/g, "");
  if (d.length <= 6) {
    // hs6: 2-2-2
    return d.replace(/^(\d{2})(\d{0,2})(\d{0,2}).*$/, (_m, a, b, c) =>
      [a, b, c].filter(Boolean).join("."),
    );
  }
  // fracción/NICO: 2-2-2-2-2
  return d.replace(/(\d{2})(?=\d)/g, "$1.");
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("es-MX");
}
