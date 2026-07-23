// app/calculadora/page.tsx — landed-cost estimator (Client Component).
//
// A guided form that POSTs to /api/calculator/estimate and renders the result.
// The UI faithfully reflects the API's honesty contract: the customs value is
// shown when computable, but IGI/DTA/IVA appear as "no confirmable" whenever the
// API returns null — the frontend never fills a gap the backend refused to.
// Fails safe: a network error shows a warning, not a crash.
"use client";

import { useState } from "react";
import Link from "next/link";
import type { Envelope } from "@schemas/envelope";
import type { EstimateResult } from "@/lib/api";
import { money } from "@/lib/format";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

const INCOTERMS = ["CIF", "CIP", "DAP", "DDP", "CFR", "CPT", "FOB", "EXW", "FCA"];

export default function CalculadoraPage() {
  const [form, setForm] = useState({
    invoice_value: 10000,
    freight: 900,
    insurance: 100,
    currency: "USD",
    incoterm: "CIF",
    input_code: "84713001",
    country_origin: "USA",
  });
  const [res, setRes] = useState<Envelope<EstimateResult> | null>(null);
  const [loading, setLoading] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/calculator/estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setRes((await r.json()) as Envelope<EstimateResult>);
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

  const d = res?.data;
  return (
    <>
      <nav className="site-nav" aria-label="Principal">
        <Link href="/" className="brand">
          AduanaMap MX
        </Link>
        <Link href="/mapa">Mapa mundial</Link>
        <Link href="/arancel">Explorador arancelario</Link>
      </nav>
      <main id="main" className="container">
        <h1>Estimador de costo aterrizado</h1>
        <p className="muted">
          El valor en aduana es determinista. Los aranceles (IGI/DTA/IVA) solo se
          muestran si existe tasa estructurada vigente; de lo contrario, se marcan
          <em> no confirmable</em>.
        </p>

        <form onSubmit={submit} className="grid cols-2">
          <div>
            <label htmlFor="invoice">Valor factura</label>
            <input
              id="invoice"
              type="number"
              min={0}
              value={form.invoice_value}
              onChange={(e) => set("invoice_value", Number(e.target.value))}
            />
          </div>
          <div>
            <label htmlFor="currency">Moneda</label>
            <input
              id="currency"
              value={form.currency}
              maxLength={3}
              onChange={(e) => set("currency", e.target.value.toUpperCase())}
            />
          </div>
          <div>
            <label htmlFor="freight">Flete</label>
            <input
              id="freight"
              type="number"
              min={0}
              value={form.freight}
              onChange={(e) => set("freight", Number(e.target.value))}
            />
          </div>
          <div>
            <label htmlFor="insurance">Seguro</label>
            <input
              id="insurance"
              type="number"
              min={0}
              value={form.insurance}
              onChange={(e) => set("insurance", Number(e.target.value))}
            />
          </div>
          <div>
            <label htmlFor="incoterm">Incoterm</label>
            <select
              id="incoterm"
              value={form.incoterm}
              onChange={(e) => set("incoterm", e.target.value)}
            >
              {INCOTERMS.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="code">Código (fracción/NICO)</label>
            <input
              id="code"
              value={form.input_code}
              onChange={(e) => set("input_code", e.target.value)}
            />
          </div>
          <div style={{ alignSelf: "end" }}>
            <button type="submit" disabled={loading}>
              {loading ? "Calculando…" : "Estimar"}
            </button>
          </div>
        </form>

        {res && (
          <section style={{ marginTop: "1.5rem" }}>
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
            {d && (
              <table>
                <tbody>
                  <tr>
                    <th>Tipo de cambio FIX</th>
                    <td>{d.mxn_exchange_rate ?? "—"}</td>
                  </tr>
                  <tr>
                    <th>Valor en aduana (MXN)</th>
                    <td>{money(d.customs_value_mxn)}</td>
                  </tr>
                  <tr>
                    <th>IGI</th>
                    <td>{d.estimated_igi_mxn === null ? "no confirmable" : money(d.estimated_igi_mxn)}</td>
                  </tr>
                  <tr>
                    <th>IVA</th>
                    <td>{d.estimated_iva_mxn === null ? "no confirmable" : money(d.estimated_iva_mxn)}</td>
                  </tr>
                  <tr>
                    <th>Trato preferencial</th>
                    <td>{d.preferential_treatment}</td>
                  </tr>
                </tbody>
              </table>
            )}
            {d?.explanation && <p className="muted">{d.explanation}</p>}
          </section>
        )}
      </main>
      <footer className="site-footer">
        <p>
          Estimación informativa. No sustituye cálculo legal ni pedimento. Cuando una
          tasa no puede confirmarse con fuente estructurada, se marca como no confirmable.
        </p>
      </footer>
    </>
  );
}
