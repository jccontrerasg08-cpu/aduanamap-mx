// components/Trace.tsx — renders an Envelope's source_trace + warnings.
//
// This is the visual half of the platform's core contract: every screen shows
// WHERE its data came from and WHAT could not be confirmed. Warnings that start
// with "no confirmable" / "no disponible" are styled as cautions. Rendering both
// blocks unconditionally keeps traceability impossible to forget on a new page.
import type { Envelope, SourceTrace } from "@schemas/envelope";
import { t, type Lang } from "@/lib/i18n";

export function Sources({ trace, lang }: { trace: SourceTrace[]; lang: Lang }) {
  if (!trace || trace.length === 0) return null;
  return (
    <p className="muted" style={{ fontSize: ".85rem" }}>
      {t(lang, "sources")}:{" "}
      {trace.map((s, i) => (
        <span key={`${s.source}-${i}`}>
          {i > 0 ? " · " : ""}
          <span className="badge">
            {s.source}
            {s.label ? ` / ${s.label}` : ""}
          </span>
        </span>
      ))}
    </p>
  );
}

export function Warnings({ warnings, lang }: { warnings: string[]; lang: Lang }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <div className="warnings" role="status" aria-live="polite">
      <strong>{t(lang, "warnings")}</strong>
      <ul>
        {warnings.map((w, i) => (
          <li key={i}>{w}</li>
        ))}
      </ul>
    </div>
  );
}

/** Convenience: render warnings + sources for any envelope in one call. */
export function Trace<T>({ env, lang }: { env: Envelope<T>; lang: Lang }) {
  return (
    <>
      <Warnings warnings={env.warnings} lang={lang} />
      <Sources trace={env.source_trace} lang={lang} />
    </>
  );
}
