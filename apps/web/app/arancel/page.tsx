// app/arancel/page.tsx — tariff explorer (HS / Fracción / NICO).
//
// Two server-rendered modes driven by search params:
//   ?q=...     full-text search over the indexed corpus (/api/tariff/search)
//   ?code=...  deterministic breakdown + versioned lookup (/api/tariff/{code})
// The breakdown (HS2→NICO10) is always shown because it is pure arithmetic; the
// catalog descriptions are shown only when the versioned tables have them, else a
// "no confirmable" warning — never an invented description.
import { apiGet, type TariffSearchRow, type TariffDetail } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";
import { Trace } from "@/components/Trace";
import { prettyCode } from "@/lib/format";

export const metadata = { title: "Explorador arancelario — AduanaMap MX" };

export default async function ArancelPage({
  searchParams,
}: {
  searchParams: { lang?: string; q?: string; code?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const q = (searchParams.q ?? "").trim();
  const code = (searchParams.code ?? "").trim();

  return (
    <Shell lang={lang}>
      <h1>{t(lang, "nav_tariff")}</h1>
      <p className="muted">Lo universal es HS (6). Lo nacional es Fracción (8) + NICO (10).</p>

      <form method="get" role="search" style={{ margin: "1rem 0" }}>
        {lang === "en" && <input type="hidden" name="lang" value="en" />}
        <label htmlFor="q">Descripción o código</label>
        <div style={{ display: "flex", gap: ".5rem" }}>
          <input id="q" name="q" defaultValue={q} placeholder="tornillo de acero…" />
          <button type="submit">{t(lang, "search")}</button>
        </div>
      </form>

      {q && (await SearchResults({ q, lang }))}
      {code && (await CodeDetail({ code, lang }))}
    </Shell>
  );
}

async function SearchResults({ q, lang }: { q: string; lang: ReturnType<typeof normalizeLang> }) {
  const env = await apiGet<TariffSearchRow[]>(
    `/api/tariff/search?q=${encodeURIComponent(q)}&lang=${lang}`,
    3600,
  );
  const rows = env.data ?? [];
  const qs = lang === "en" ? "&lang=en" : "";
  return (
    <section>
      <Trace env={env} lang={lang} />
      {rows.length === 0 ? (
        <p className="card">Sin coincidencias en el índice.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nivel</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.display_code}-${i}`}>
                <td className="mono">
                  <a href={`/arancel?code=${r.display_code}${qs}`}>{prettyCode(r.display_code)}</a>
                </td>
                <td>{r.level}</td>
                <td>{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

async function CodeDetail({ code, lang }: { code: string; lang: ReturnType<typeof normalizeLang> }) {
  const env = await apiGet<TariffDetail>(`/api/tariff/${encodeURIComponent(code)}?lang=${lang}`, 3600);
  const d = env.data;
  const n = d?.normalize;
  return (
    <section>
      <h2>{prettyCode(code)}</h2>
      {n && (
        <table>
          <tbody>
            <tr><th>HS2</th><td className="mono">{n.hs2 ?? "—"}</td></tr>
            <tr><th>HS4</th><td className="mono">{n.hs4 ?? "—"}</td></tr>
            <tr><th>HS6</th><td className="mono">{n.hs6 ?? "—"}</td></tr>
            <tr><th>Fracción</th><td className="mono">{n.fraccion8 ?? "—"}</td></tr>
            <tr><th>NICO</th><td className="mono">{n.nico10 ?? "—"}</td></tr>
          </tbody>
        </table>
      )}
      {d?.hs6 && (
        <p className="card">
          <strong>HS6:</strong> {d.hs6.description_es}{" "}
          <span className="badge">HS {d.hs6.hs_version}</span>
        </p>
      )}
      {d?.fraccion && (
        <p className="card">
          <strong>Fracción:</strong> {d.fraccion.description_es}{" "}
          <span className="badge">LIGIE {d.fraccion.ligie_version}</span>
        </p>
      )}
      <Trace env={env} lang={lang} />
    </section>
  );
}
