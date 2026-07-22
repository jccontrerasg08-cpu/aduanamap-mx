// layout.tsx — Next.js App Router root layout.
// Wraps every page in the <html lang="es"> shell and exports the default
// bilingual site metadata (title/description) used for SEO and social cards.
// Individual routes override `metadata` as needed.
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
      <body>{children}</body>
    </html>
  );
}
