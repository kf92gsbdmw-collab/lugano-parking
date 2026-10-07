/* Lugano Parking service worker: instant reopen and offline map. Bump VERSION when files change. */
const VERSION = "lp-2026-10-07c";
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"];
const TILES = ["tiles/z15.jpg", "tiles/z14.jpg", "tiles/z16.jpg", "tiles/z17.jpg"];

self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(VERSION);
    await c.addAll(CORE);
    // Map tiles are large: fetch them one by one and never let a failure block the install.
    for (const t of TILES) { try { await c.add(t); } catch (_) {} }
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== VERSION) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Live feed from the city: always straight to the network.
  if (url.hostname.endsWith("lugano.ch")) return;
  const sameOrigin = url.origin === self.location.origin;
  const isFont = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  const isLib = url.hostname === "cdnjs.cloudflare.com";
  if (!sameOrigin && !isFont && !isLib) return;

  // Map tiles, icons, Leaflet: cache first (immutable).
  if (url.pathname.includes("/tiles/") || isLib || /\.(png|webmanifest)$/.test(url.pathname)) {
    e.respondWith(cacheFirst(req)); return;
  }
  // The app shell and fonts: serve the cached copy instantly, refresh it in the background.
  e.respondWith(staleWhileRevalidate(req));
});

async function cacheFirst(req) {
  const c = await caches.open(VERSION);
  const hit = await c.match(req, { ignoreSearch: true }); if (hit) return hit;
  const res = await fetch(req); if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone());
  return res;
}
async function staleWhileRevalidate(req) {
  const c = await caches.open(VERSION);
  const hit = await c.match(req, { ignoreSearch: true });
  const net = fetch(req).then(res => { if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone()); return res; }).catch(() => null);
  return hit || (await net) || Response.error();
}
