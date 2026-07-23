// components/Shell.tsx — per-page chrome: Nav + <main> landmark + Disclaimer.
// Pages resolve `lang` from ?lang= and wrap their content in <Shell lang>. The
// <main id="main"> is the skip-link target defined in the root layout.
import type { ReactNode } from "react";
import { Nav } from "@/components/Nav";
import { Disclaimer } from "@/components/Disclaimer";
import type { Lang } from "@/lib/i18n";

export function Shell({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <>
      <Nav lang={lang} />
      <main id="main" className="container">
        {children}
      </main>
      <Disclaimer lang={lang} />
    </>
  );
}
