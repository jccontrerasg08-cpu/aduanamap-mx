// components/Disclaimer.tsx — legal disclaimer shown in the footer of every page.
// The exact wording is the platform's non-negotiable stance: informational only,
// and "no confirmable" when a source can't back a value. Text lives in i18n.
import { t, type Lang } from "@/lib/i18n";

export function Disclaimer({ lang }: { lang: Lang }) {
  return (
    <footer className="site-footer">
      <p>{t(lang, "disclaimer")}</p>
    </footer>
  );
}
