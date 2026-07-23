// app/mapa/page.tsx — world "map" as an accessible, WebGL-independent country list.
//
// The report is explicit: the map's accessibility must not depend on the WebGL
// canvas, so the country TABLE is the PRIMARY, keyboard-usable view. The MapLibre
// <WorldMap> below is a progressive enhancement over the same /api/map/countries
// data. Server-rendered; degrades to a warning if the catalog is empty or down.
import Link from "next/link";
import { apiGet, type MapCountry } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";
import { Trace } from "@/components/Trace";
import { WorldMap } from "@/components/WorldMap";

export const metadata = { title: "Mapa mundial — AduanaMap MX" };

export default async function MapaPage({
  searchParams,
}: {
  searchParams: { lang?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const q = lang === "en" ? "?lang=en" : "";
  const env = await apiGet<MapCountry[]>(`/api/map/countries?lang=${lang}`, 3600);
  const countries = env.data ?? [];

  return (
    <Shell lang={lang}>
      <h1>{t(lang, "nav_map")}</h1>
      <p className="muted">
        La tabla es la vista principal, accesible y navegable por teclado. El mapa de
        abajo es una mejora visual (MapLibre) sobre los mismos datos; las fronteras
        siguen a Natural Earth y no constituyen una postura política.
      </p>

      <WorldMap countries={countries} />

      <Trace env={env} lang={lang} />

      {countries.length === 0 ? (
        <p className="card">Aún no hay países cargados en el catálogo.</p>
      ) : (
        <table>
          <caption className="muted" style={{ textAlign: "left", marginBottom: ".5rem" }}>
            {countries.length} {t(lang, "countries").toLowerCase()}
          </caption>
          <thead>
            <tr>
              <th>ISO3</th>
              <th>{t(lang, "countries")}</th>
              <th>{t(lang, "agreements")}</th>
            </tr>
          </thead>
          <tbody>
            {countries.map((c) => (
              <tr key={c.iso3}>
                <td className="mono">{c.iso3}</td>
                <td>
                  <Link href={`/pais/${c.iso3.toLowerCase()}${q}`}>{c.name}</Link>
                </td>
                <td>{c.agreements_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
