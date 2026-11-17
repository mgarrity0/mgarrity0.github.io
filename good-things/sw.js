// sw.js: service worker for "3 Good Things" (garritymade.com/good-things/).
//
// Caches the app shell so the Spiralling? tab opens offline. The log itself
// lives on claude.ai and is never cached here.
// Bump CACHE_VERSION on any deploy that changes a precached file; activate()
// deletes this app's caches from older versions. Only caches named
// "goodthings-*" are touched, so the rock's caches on the same origin are safe.
const CACHE_VERSION = 'v1';
const SHELL_CACHE = `goodthings-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `goodthings-runtime-${CACHE_VERSION}`;

const SHELL_FILES = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => Promise.all(SHELL_FILES.map((f) => cache.add(f).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((k) => k.startsWith('goodthings-') && k !== SHELL_CACHE && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const scopePath = new URL(self.registration.scope).pathname;

  // This app's own files: navigations network-first (so deploys show up),
  // everything else cache-first.
  if (url.origin === self.location.origin && url.pathname.startsWith(scopePath)) {
    if (req.mode === 'navigate') {
      event.respondWith(
        fetch(req)
          .then((res) => {
            if (res.ok) {
              const copy = res.clone();
              caches.open(SHELL_CACHE).then((c) => c.put('./index.html', copy));
            }
            return res;
          })
          .catch(() => caches.match('./index.html', { ignoreSearch: true }))
      );
      return;
    }
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(RUNTIME_CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }))
    );
    return;
  }

  // Google Fonts: serve the cached copy if there is one, refresh in the background.
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        const net = fetch(req)
          .then((res) => {
            if (res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(() => hit);
        return hit || net;
      })
    );
  }
  // Everything else (claude.ai included) goes straight to the network.
});
