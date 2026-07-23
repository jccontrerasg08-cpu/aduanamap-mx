// app/fuentes/page.tsx — public ETL/source freshness page.
//
// The report lists "Fuentes" as a core screen and makes operation visible a P0:
// anyone can see which official source last loaded, when, and whether it is stale.
// That transparency is the product's trust mechanism — the same reason every
// response carries source_trace.
//
// Reads /api/sources/status and /api/healthz in parallel. Both degrade: with no DB
// the page renders the warning from the envelope instead of failing.
import { apiGet, type HealthDoc } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";
import { Trace } from "@/components/Trace";
import { fmtDate } from "@/lib/format";

export const metadata = {
  title: "Fuentes y frescura de datos",
  description:
    "Estatus de las fuentes oficiales (ANAM, SNICE, VUCEM, DOF, Banxico): última carga exitosa y frescura.",
};

interface SourceRow {
  source: string;
  status: string;
  last_success: string | null;
}

const LABELS: Record<string, string> = {
  banxico: "Banxico (SIE / FIX)",
  snice: "SNICE (LIGIE / NICO)",
  vucem: "VUCEM (clasificador)",
  anam: "ANAM (tratados / guías)",
  dof: "DOF (comercio exterior)",
  seed_countries: "Catálogo de países",
  "world-atlas-50m": "Geometría de países",
};

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "ok" ? "var(--accent)" : status === "error" ? "#b3261e" : "var(--warn-fg)";
  return (
    <span className="badge" style={{ borderColor: tone, color: tone }}>
      {status}
    </span>
  );
}

export default async function FuentesPage({
  searchParams,
}: {
  searchParams: { lang?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const [sourcesEnv, healthEnv] = await Promise.all([
    apiGet<SourceRow[]>("/api/sources/status", 300),
    apiGet<HealthDoc>("/api/healthz", 30),
  ]);
  const rows = sourcesEnv.data ?? [];
  const deps = healthEnv.data?.dependencies ?? {};

  return (
    <Shell lang={lang}>
      <h1>{t(lang, "sources")}</h1>
      <p className="muted">
        Cada dato de la plataforma proviene de una fuente oficial versionada. Aquí puedes
        ver cuándo se cargó por última vez cada una. Si una fuente está <em>stale</em>, la
        plataforma sigue sirviendo el último snapshot válido y lo advierte.
      </p>

      <Trace env={sourcesEnv} lang={lang} />

      <h2>Fuentes oficiales</h2>
      {rows.length === 0 ? (
        <p className="card">
          Aún no hay corridas ETL registradas. Ejecuta un worker (p. ej.{" "}
          <code className="mono">python -m workers.seed_countries</code>) con la base de
          datos activa.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Fuente</th>
              <th>Estatus</th>
              <th>Última carga exitosa</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.source}>
                <td>{LABELS[r.source] ?? r.source}</td>
                <td>
                  <StatusBadge status={r.status} />
                </td>
                <td>{fmtDate(r.last_success)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>Dependencias del sistema</h2>
      {Object.keys(deps).length === 0 ? (
        <p className="card">API no disponible.</p>
      ) : (
        <ul>
          {Object.entries(deps).map(([name, status]) => (
            <li key={name}>
              {name}: <StatusBadge status={status} />
            </li>
          ))}
        </ul>
      )}
    </Shell>
  );
}
