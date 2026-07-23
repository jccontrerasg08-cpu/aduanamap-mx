// app/page.tsx — public landing (Server Component).
// Bilingual hero + section entry points, and a live API status probe. Everything
// degrades: if the API is down, apiGet returns an offline envelope and the page
// still renders with an "unavailable" badge instead of failing.
import Link from "next/link";
import { apiGet, type HealthDoc } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";

export default async function Home({
  searchParams,
}: {
  searchParams: { lang?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const q = lang === "en" ? "?lang=en" : "";
  const health = await apiGet<HealthDoc>("/api/healthz", 30);
  const status = health.data?.status;

  return (
    <Shell lang={lang}>
      <h1>AduanaMap MX / TradeWiki MX</h1>
      <p style={{ fontSize: "1.1rem" }}>{t(lang, "tagline")}</p>

      <div className="grid cols-2" style={{ marginTop: "2rem" }}>
        <Link href={`/mapa${q}`} className="card">
          <h2>🗺️ {t(lang, "nav_map")}</h2>
          <p className="muted">Relación de cada país con México: TLC, APPRIs, acuerdos.</p>
        </Link>
        <Link href={`/arancel${q}`} className="card">
          <h2>🔎 {t(lang, "nav_tariff")}</h2>
          <p className="muted">HS (6) universal → Fracción (8) → NICO (10) nacional.</p>
        </Link>
        <Link href={`/calculadora${q}`} className="card">
          <h2>🧮 {t(lang, "nav_calc")}</h2>
          <p className="muted">Valor en aduana determinista; nunca inventa aranceles.</p>
        </Link>
      </div>

      <p className="muted" style={{ marginTop: "2rem" }}>
        {t(lang, "api_status")}:{" "}
        {status ? (
          <span className="badge">
            {status} · v{health.data?.version}
          </span>
        ) : (
          <span className="badge">{t(lang, "unavailable")}</span>
        )}
      </p>
    </Shell>
  );
}
