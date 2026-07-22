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
