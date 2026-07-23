// app/robots.ts — generates /robots.txt (report §SEO técnico).
//
// Allows the public reference content and points crawlers at the sitemap.
// Disallows admin surfaces and ephemeral/parameterized result pages, which the
// report explicitly says should not be indexed (they'd create duplicate,
// low-value URLs — e.g. every tariff search query string).
import type { MetadataRoute } from "next";

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin", "/api/", "/arancel?", "/*?q="],
      },
    ],
    sitemap: `${BASE}/sitemap.xml`,
    host: BASE,
  };
}
