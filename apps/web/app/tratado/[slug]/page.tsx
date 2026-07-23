// app/tratado/[slug]/page.tsx — agreement (tratado) detail / wiki card.
// Shows members, dates and source documents. Absent slug → graceful not-found
// via the API's "no confirmable" warning, never an invented treaty.
import Link from "next/link";
import { apiGet, type AgreementDetail } from "@/lib/api";
import { normalizeLang, t } from "@/lib/i18n";
import { Shell } from "@/components/Shell";
import { Trace, Warnings } from "@/components/Trace";
import { fmtDate } from "@/lib/format";

export default async function TratadoPage({
  params,
  searchParams,
}: {
  params: { slug: string };
  searchParams: { lang?: string };
}) {
  const lang = normalizeLang(searchParams.lang);
  const q = lang === "en" ? "?lang=en" : "";
  const env = await apiGet<AgreementDetail>(`/api/agreements/${params.slug}?lang=${lang}`, 3600);
  const a = env.data;

  return (
    <Shell lang={lang}>
      <p>
        <Link href={`/mapa${q}`}>← {t(lang, "nav_map")}</Link>
      </p>

      {!a ? (
        <>
          <h1 className="mono">{params.slug}</h1>
          <Warnings warnings={env.warnings} lang={lang} />
          <p className="card">Tratado no encontrado en el catálogo.</p>
        </>
      ) : (
        <>
          <h1>{a.name}</h1>
          <p>
            <span className="badge">{a.type ?? "—"}</span>{" "}
            <span className="badge">{a.status ?? "—"}</span>
          </p>
          <div className="grid cols-2">
            <div className="card">
              <p>
                <strong>{t(lang, "members")}:</strong>{" "}
                {a.members.map((m, i) => (
                  <span key={m}>
                    {i > 0 ? ", " : ""}
                    <Link href={`/pais/${m.toLowerCase()}${q}`} className="mono">
                      {m}
                    </Link>
                  </span>
                ))}
              </p>
              <p>
                <strong>Firmado:</strong> {fmtDate(a.signed_date)} ·{" "}
                <strong>{t(lang, "effective")}:</strong> {fmtDate(a.effective_date)}
              </p>
            </div>
          </div>

          {a.documents.length > 0 && (
            <>
              <h2>Documentos fuente</h2>
              <ul>
                {a.documents.map((d) => (
                  <li key={d.document_id}>
                    {d.title} <span className="badge">{d.kind}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      <Trace env={env} lang={lang} />
    </Shell>
  );
}
