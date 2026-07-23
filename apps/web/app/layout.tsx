// layout.tsx — Next.js App Router root layout.
// Provides the <html>/<body> shell, imports global styles, and adds an
// accessibility skip-link. It stays lang-agnostic because the root layout cannot
// read the ?lang= search param — per-page content is wrapped in <Shell lang> which
// renders the nav + footer. Exports the default bilingual SEO metadata.
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const TITLE = "AduanaMap MX / TradeWiki MX";
const DESCRIPTION =
  "Mapa mundial, wiki jurídica-operativa y explorador arancelario (HS / Fracción / NICO) de México, con trazabilidad de fuentes oficiales.";

// metadataBase makes every canonical/OG URL absolute. `alternates.languages`
// emits the hreflang es/en pair the report requires; routes inherit and can
// override. OpenGraph/Twitter give shareable cards per the SEO checklist.
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: `%s — AduanaMap MX` },
  description: DESCRIPTION,
  applicationName: "AduanaMap MX",
  alternates: {
    canonical: "/",
    languages: { es: "/", en: "/?lang=en" },
  },
  openGraph: {
    type: "website",
    siteName: "AduanaMap MX",
    locale: "es_MX",
    alternateLocale: ["en_US"],
    title: TITLE,
    description: DESCRIPTION,
    url: "/",
  },
  twitter: { card: "summary_large_image", title: TITLE, description: DESCRIPTION },
  robots: { index: true, follow: true },
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
