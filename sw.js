/* Lugano Parking service worker: instant reopen and offline map. Bump VERSION when files change. */
const VERSION = "lp-2026-10-08b";
const MAPCACHE = "lp-map-v1"; // vector tiles, fonts and sprites from OpenFreeMap, kept across app versions
const MAPCACHE_MAX = 800;
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png", "logo.svg",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js",
  "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.js",
  "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.css"];
const TILES = ["tiles/z15.jpg", "tiles/z14.jpg", "tiles/z16.jpg", "tiles/z17.jpg"]; // or zNN.jpg at the root, cached on first use

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
    for (const k of await caches.keys()) if (k !== VERSION && k !== MAPCACHE) await caches.delete(k);
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
  const isMap = url.hostname === "tiles.openfreemap.org";
  if (!sameOrigin && !isFont && !isLib && !isMap) return;

  // OpenFreeMap: cache what has been seen so the last viewed area still draws offline (style JSON stays fresh).
  if (isMap) { e.respondWith(url.pathname.startsWith("/styles/") ? staleWhileRevalidate(req, MAPCACHE) : cacheFirst(req, MAPCACHE, true)); return; }

  // Map tiles, icons, Leaflet: cache first (immutable).
  if (/\/(tiles\/)?z1[4-7]\.jpg$/.test(url.pathname) || isLib || /\.(png|svg|webmanifest)$/.test(url.pathname)) {
    e.respondWith(cacheFirst(req)); return;
  }
  // The app itself: try the network first (so a new upload shows up on the next open), fall back to the cached copy offline.
  if (sameOrigin && (req.mode === "navigate" || /\/(index\.html)?$/.test(url.pathname))) { e.respondWith(networkFirst(req)); return; }
  // Fonts: serve the cached copy instantly, refresh it in the background.
  e.respondWith(staleWhileRevalidate(req));
});

async function networkFirst(req) {
  const c = await caches.open(VERSION);
  try {
    const ctrl = new AbortController(); const t = setTimeout(() => ctrl.abort(), 4000);
    const res = await fetch(req, { signal: ctrl.signal, cache: "no-store" }); clearTimeout(t);
    if (res && res.ok) { c.put(req, res.clone()); return res; }
    throw new Error("bad response");
  } catch (_) {
    return (await c.match(req, { ignoreSearch: true })) || (await c.match("./")) || Response.error();
  }
}

async function cacheFirst(req, name, trim) {
  const c = await caches.open(name || VERSION);
  const hit = await c.match(req, { ignoreSearch: true }); if (hit) return hit;
  const res = await fetch(req); if (res && (res.ok || res.type === "opaque")) { c.put(req, res.clone()); if (trim) trimCache(c); }
  return res;
}
let trimming = false;
async function trimCache(c) {
  if (trimming) return; trimming = true;
  try { const keys = await c.keys(); if (keys.length > MAPCACHE_MAX) for (const k of keys.slice(0, keys.length - MAPCACHE_MAX)) await c.delete(k); }
  finally { trimming = false; }
}
async function staleWhileRevalidate(req, name) {
  const c = await caches.open(name || VERSION);
  const hit = await c.match(req, { ignoreSearch: true });
  const net = fetch(req).then(res => { if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone()); return res; }).catch(() => null);
  return hit || (await net) || Response.error();
}
