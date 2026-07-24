// components/Nav.tsx — top site navigation, present on every page via layout.
// Server component; links carry the current ?lang= so the choice persists.
import Link from "next/link";
import { t, type Lang } from "@/lib/i18n";

export function Nav({ lang }: { lang: Lang }) {
  const q = lang === "en" ? "?lang=en" : "";
  const other = lang === "en" ? "es" : "en";
  return (
    <nav className="site-nav" aria-label="Principal">
      <Link href={`/${q}`} className="brand">
        {process.env.NEXT_PUBLIC_SITE_NAME ?? "AduanaMap MX"}
      </Link>
      <Link href={`/mapa${q}`}>{t(lang, "nav_map")}</Link>
      <Link href={`/arancel${q}`}>{t(lang, "nav_tariff")}</Link>
      <Link href={`/calculadora${q}`}>{t(lang, "nav_calc")}</Link>
      <Link href={`/asistente${q}`}>Asistente</Link>
      <Link href={`/fuentes${q}`}>{t(lang, "sources")}</Link>
      <Link href={`?lang=${other}`} className="badge" aria-label={`Switch language to ${other}`}>
        {other.toUpperCase()}
      </Link>
    </nav>
  );
}
