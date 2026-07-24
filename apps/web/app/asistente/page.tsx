// app/asistente/page.tsx — grounded trade assistant UI (Client Component).
//
// Thin shell over POST /api/assistant/ask. The assistant answers only from the
// canonical catalogue and returns its sources, so this page always renders the
// answer TOGETHER with source_trace + warnings — the user can see what backs the
// claim, and when the assistant declines (rates / rules of origin) that refusal is
// shown verbatim. The UI never adds facts of its own.
"use client";

import { useState } from "react";
import Link from "next/link";
import type { Envelope } from "@schemas/envelope";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

interface AskData {
  answer: string;
  grounded: boolean;
  detail: Record<string, unknown>;
}

const EXAMPLES = [
  "¿México tiene TLC con Japón?",
  "¿Cuántos TLC tiene México?",
  "Háblame del T-MEC",
  "¿TLC con Alemania?",
  "¿Cuánto arancel pago por tornillos?",
];

export default function AsistentePage() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<Envelope<AskData> | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask(question: string) {
    const text = question.trim();
    if (!text) return;
    setQ(text);
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/assistant/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, lang: "es" }),
      });
      setRes((await r.json()) as Envelope<AskData>);
    } catch {
      setRes({
        data: null,
        source_trace: [],
        warnings: ["no disponible: no se pudo contactar la API"],
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <nav className="site-nav" aria-label="Principal">
        <Link href="/" className="brand">
          AduanaMap MX
        </Link>
        <Link href="/mapa">Mapa mundial</Link>
        <Link href="/arancel">Explorador arancelario</Link>
        <Link href="/calculadora">Calculadora</Link>
        <Link href="/fuentes">Fuentes</Link>
      </nav>
      <main id="main" className="container">
        <h1>Asistente de comercio exterior</h1>
        <p className="muted">
          Responde sobre los tratados de libre comercio de México citando la fuente.
          No afirma aranceles, IVA ni reglas de origen: para eso usa el{" "}
          <Link href="/arancel">explorador arancelario</Link> y la{" "}
          <Link href="/calculadora">calculadora</Link>, que muestran la fuente estructurada.
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(q);
          }}
          role="search"
        >
          <label htmlFor="q">Tu pregunta</label>
          <div style={{ display: "flex", gap: ".5rem" }}>
            <input
              id="q"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="¿México tiene TLC con Japón?"
              maxLength={500}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Consultando…" : "Preguntar"}
            </button>
          </div>
        </form>

        <p className="muted" style={{ marginTop: ".75rem", fontSize: ".9rem" }}>
          Ejemplos:{" "}
          {EXAMPLES.map((ex, i) => (
            <span key={ex}>
              {i > 0 ? " · " : ""}
              <button
                type="button"
                onClick={() => ask(ex)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  padding: 0,
                  cursor: "pointer",
                  font: "inherit",
                  textDecoration: "underline",
                }}
              >
                {ex}
              </button>
            </span>
          ))}
        </p>

        {res && (
          <section style={{ marginTop: "1.5rem" }} aria-live="polite">
            {res.data?.answer && (
              <div className="card">
                <p style={{ margin: 0 }}>{res.data.answer}</p>
              </div>
            )}

            {res.warnings.length > 0 && (
              <div className="warnings" role="status">
                <strong>Advertencias</strong>
                <ul>
                  {res.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {res.source_trace.length > 0 && (
              <p className="muted" style={{ fontSize: ".85rem" }}>
                Fuentes:{" "}
                {res.source_trace.map((s, i) => (
                  <span key={`${s.source}-${i}`}>
                    {i > 0 ? " · " : ""}
                    <span className="badge">
                      {s.source}
                      {s.label ? ` / ${s.label}` : ""}
                    </span>
                  </span>
                ))}
              </p>
            )}
          </section>
        )}
      </main>
      <footer className="site-footer">
        <p>
          Herramienta informativa y educativa. No constituye asesoría legal, fiscal ni
          aduanera. El asistente solo afirma lo que puede respaldar con su catálogo de
          fuentes; cuando algo no puede confirmarse, lo dice explícitamente.
        </p>
      </footer>
    </>
  );
}
