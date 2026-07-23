/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_SITE_NAME: process.env.NEXT_PUBLIC_SITE_NAME ?? "AduanaMap MX",
    API_BASE_URL: process.env.API_BASE_URL ?? "http://localhost:8000",
    // Public origin used for canonical URLs, hreflang, sitemap and OG cards.
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  },
};

export default nextConfig;
