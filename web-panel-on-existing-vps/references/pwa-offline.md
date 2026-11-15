# PWA for a served SPA: installable + offline

Applies to a Vite/React app already served under a path prefix on a shared VPS
(see the SPA section in SKILL.md). `vite-plugin-pwa` generates the manifest and
service worker; the remaining work is making prefix, caching and offline data
agree.

## Setup

`npm i -D vite-plugin-pwa`, then in `vite.config.ts`:

```ts
import { VitePWA } from "vite-plugin-pwa";
// base must already be "/prefix/"
VitePWA({
  registerType: "autoUpdate",
  injectRegister: "auto",
  manifest: {
    name: "...", short_name: "...",
    theme_color: "#05070d", background_color: "#05070d",
    display: "standalone", orientation: "portrait",
    start_url: "/prefix/", scope: "/prefix/", lang: "ru",
    icons: [
      { src: "/prefix/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/prefix/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/prefix/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  },
  workbox: {
    globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
    navigateFallback: "/prefix/index.html",
    navigateFallbackDenylist: [/^\/prefix-api/, /^\/prefix-pub/],
  },
  devOptions: { enabled: false },
})
```

- Icon paths and `start_url`/`scope` carry the prefix — the plugin reads `base`
  for the build, but the manifest values are literal strings you write.
- `navigateFallbackDenylist` must exclude the API prefixes, or an API 404 gets
  answered with `index.html`.

## Icons

`npm i -D sharp`; one `make-icons.mjs` (the `.mjs` extension matters — the
project is `"type": "module"`, so `require` throws):

```js
import sharp from "sharp";
await sharp("public/icon.svg").resize(192,192).png().toFile("public/icon-192.png");
await sharp("public/icon.svg").resize(512,512).png().toFile("public/icon-512.png");
// maskable: pad the glyph inside the safe zone on a solid background
await sharp({ create: { width: 512, height: 512, channels: 4, background: {r:13,g:20,b:36,alpha:1} } })
  .composite([{ input: await sharp("public/icon.svg").resize(360,360).png().toBuffer(), gravity: "center" }])
  .png().toFile("public/icon-maskable-512.png");
```

## Static-server duties

- `.webmanifest` → `application/manifest+json` (the default octet-stream makes
  some browsers ignore the manifest).
- Cache policy — the part that decides whether updates ever reach clients:

  | path | Cache-Control |
  |---|---|
  | `sw.js`, `registerSW.js`, `manifest.webmanifest`, `workbox-*` | `no-store` |
  | `assets/*` (hashed names) | `max-age=31536000, immutable` |
  | `index.html` and everything else | `no-store` |

  A cached SW or manifest pins the old app until the user clears site data.

## Offline data

The service worker precaches the app shell; dynamic data (tenant, services,
gallery) must be cached in the data layer:

- `localStorage` entries `avto-cache:<key>` = `{ts, data}`, TTL 24h, pruned on
  read.
- Check `navigator.onLine === false` **before** issuing the request.
  `supabase-js` exposes no `AbortSignal`, and offline it hangs pending forever
  instead of rejecting — a `catch` fallback never runs.
- Wrap the call in `Promise.race([query, timeout(6000)])` as the second guard,
  and treat a timeout the same as offline.
- Render an offline banner whenever `navigator.onLine` is false; a cached page
  that looks live teaches the client the wrong thing.

## TanStack Query traps

- `networkMode: 'offlineFirst'` **breaks** this pattern: the `queryFn` is not
  called while offline, so the data-layer cache fallback cannot execute and the
  page sits on `isLoading`. Keep the default network mode.
- `experimental_createQueryPersister` does not satisfy
  `defaultOptions.persister` (its type mismatches the query-function
  signature); the hand-rolled localStorage fallback in the fetch layer is less
  friction.

## Offline verification

`Network.emulateNetworkConditions` does **not** change `navigator.onLine` — an
"offline" tab still reports `onLine: true`, so onLine-gated code never triggers
and only the timeout path fires, seconds later and after TanStack's `retry`.
To test honestly:

```python
cdp("Page.addScriptToEvaluateOnNewDocument",
    source="Object.defineProperty(navigator, 'onLine', { get: () => false, configurable: true });")
cdp("Network.emulateNetworkConditions", offline=True, latency=0, downloadThroughput=0, uploadThroughput=0)
# navigate, wait, assert: hero + services + price render from cache, banner visible
# then emulate online again and confirm a clean tab shows live data with no banner
```

Use the exact CDP parameter names (`downloadThroughput`, not a misspelling) or
CDP answers `-32602 Invalid parameters`.
