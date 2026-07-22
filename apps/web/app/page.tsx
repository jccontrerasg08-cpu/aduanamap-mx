// page.tsx — public landing page (Server Component).
// Renders the bilingual hero + section nav (mapa, arancel, calculadora) and
// probes the API's /api/healthz to show live system status. getHealth() degrades
// to null on any fetch error so the page always renders, even with the API down.
async function getHealth() {
  const base = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/healthz`, { cache: "no-store" });
    return (await res.json()) as { status: string; version: string };
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getHealth();
  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "3rem 1.5rem", fontFamily: "system-ui" }}>
      <h1>AduanaMap MX / TradeWiki MX</h1>
      <p>
        Mundo → país → instrumento → código → cálculo → <strong>fuente</strong>. Plataforma pública y
        bilingüe de comercio exterior de México con trazabilidad de fuentes oficiales.
      </p>

      <nav aria-label="Secciones principales" style={{ display: "grid", gap: 12, margin: "2rem 0" }}>
        <a href="/mapa">🗺️ Mapa mundial — relación con México</a>
        <a href="/arancel">🔎 Explorador arancelario — HS / Fracción / NICO</a>
        <a href="/calculadora">🧮 Estimador de costo aterrizado</a>
      </nav>

      <section aria-label="Estado del sistema" style={{ fontSize: 14, color: "#555" }}>
        Estado de la API:{" "}
        {health ? <code>{health.status} · v{health.version}</code> : <code>no disponible</code>}
      </section>

      <footer style={{ marginTop: "3rem", fontSize: 12, color: "#777" }}>
        Herramienta informativa y educativa. No constituye asesoría legal, fiscal ni aduanera. Cuando una
        preferencia o tasa no puede confirmarse con fuente estructurada, se marca como <em>no confirmable</em>.
      </footer>
    </main>
  );
}
