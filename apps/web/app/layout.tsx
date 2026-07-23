// layout.tsx — Next.js App Router root layout.
// Provides the <html>/<body> shell, imports global styles, and adds an
// accessibility skip-link. It stays lang-agnostic because the root layout cannot
// read the ?lang= search param — per-page content is wrapped in <Shell lang> which
// renders the nav + footer. Exports the default bilingual SEO metadata.
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "AduanaMap MX / TradeWiki MX",
  description:
    "Mapa mundial, wiki jurídica-operativa y explorador arancelario (HS / Fracción / NICO) de México, con trazabilidad de fuentes oficiales.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>
        <a href="#main" className="skip-link">
          Saltar al contenido
        </a>
        {children}
      </body>
    </html>
  );
}
