import type { CapacitorConfig } from "@capacitor/cli";

// This app shell doesn't ship a bundled web build — it loads the deployed
// Next.js site directly (server.url below), the same way a browser would.
// That's the simplest correct setup for a site that fetches fresh data
// per-request (ratings/fixtures change daily) rather than a static export.
//
// Before building for real, replace PRODUCTION_URL with your actual Vercel
// domain once Phase 2 is deployed.
const PRODUCTION_URL = "https://REPLACE-WITH-YOUR-VERCEL-DOMAIN.vercel.app";

const config: CapacitorConfig = {
  appId: "com.gambitparlay.app",
  appName: "gambitParlay",
  webDir: "www",
  server: {
    url: PRODUCTION_URL,
    // The remote site is always HTTPS (Vercel), so cleartext traffic is
    // never needed and stays disabled.
    cleartext: false,
  },
  ios: {
    contentInset: "automatic",
  },
};

export default config;
