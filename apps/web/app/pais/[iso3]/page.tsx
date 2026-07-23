// app/pais/[iso3]/page.tsx — country profile.
// Fetches the profile and its agreements in parallel. If the country isn't in the
// catalog the API returns data:null + a "no confirmable" warning, which we render
// as a graceful not-found state (never a fabricated profile).
import Link from "next/link";
import { apiGet, type CountryProfile, type AgreementRow } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";
import { Trace, Warnings } from "@/components/Trace";
import { fmtDate } from "@/lib/format";

export default async function PaisPage({
  params,
  searchParams,
}: {
  params: { iso3: string };
  searchParams: { lang?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const q = lang === "en" ? "?lang=en" : "";
  const iso3 = params.iso3.toUpperCase();

  const [profileEnv, agreementsEnv] = await Promise.all([
    apiGet<CountryProfile>(`/api/countries/${iso3}?lang=${lang}`, 3600),
    apiGet<AgreementRow[]>(`/api/countries/${iso3}/agreements?lang=${lang}`, 3600),
  ]);

  const p = profileEnv.data;
  const agreements = agreementsEnv.data ?? [];

  return (
    <Shell lang={lang}>
      <p>
        <Link href={`/mapa${q}`}>← {t(lang, "nav_map")}</Link>
      </p>

      {!p ? (
        <>
          <h1>{iso3}</h1>
          <Warnings warnings={profileEnv.warnings} lang={lang} />
          <p className="card">País no encontrado en el catálogo.</p>
        </>
      ) : (
        <>
          <h1>
            {p.name} <span className="muted mono">{p.iso3}</span>
          </h1>
          <div className="grid cols-2">
            <div className="card">
              <p>
                <strong>{t(lang, "region")}:</strong> {p.region ?? "—"}
                {p.subregion ? ` · ${p.subregion}` : ""}
              </p>
              <p>
                <strong>{t(lang, "agreements")}:</strong>{" "}
                {p.has_preferential_agreement ? p.agreements.length : 0}
              </p>
            </div>
          </div>

          <h2>{t(lang, "agreements")}</h2>
          {agreements.length === 0 ? (
            <p className="muted">Sin instrumentos registrados.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>{t(lang, "agreements")}</th>
                  <th>Tipo</th>
                  <th>{t(lang, "effective")}</th>
                </tr>
              </thead>
              <tbody>
                {agreements.map((a) => (
                  <tr key={a.slug}>
                    <td>
                      <Link href={`/tratado/${a.slug}${q}`}>{a.name}</Link>
                    </td>
                    <td>{a.type ?? "—"}</td>
                    <td>{fmtDate(a.effective_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      <Trace env={profileEnv} lang={lang} />
    </Shell>
  );
}
