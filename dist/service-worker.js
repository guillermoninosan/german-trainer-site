// German Trainer - service worker
//
// Bump CACHE_VERSION every time you redeploy (new data.json / new features) so
// installed devices pick up the new index.html instead of serving a stale cached
// copy forever. See README.md "Redeploying" for the one-line rule.
const CACHE_VERSION = 'v-dc7962554d';
const CACHE_NAME = `german-trainer-${CACHE_VERSION}`;

// Same-origin app shell: cached eagerly on install so the app opens with zero
// network requests (true airplane-mode / cold-start offline).
const PRECACHE_URLS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
];

// Firebase SDK files: also same-origin-cacheable (served from a CDN but fetched
// with CORS), pinned by version in the URL so caching them is safe. Once cached,
// sign-in UI + the app can load fully offline; Firestore itself will simply queue
// writes/read from its own local cache until the device is back online.
const FIREBASE_URLS = [
  'https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js',
  'https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(
        [...PRECACHE_URLS, ...FIREBASE_URLS].map((url) =>
          cache.add(new Request(url, { cache: 'reload' })).catch(() => {})
        )
      )
    )
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Let the page force an immediate takeover after showing an "update available" banner.
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // never intercept Firestore/Auth POSTs etc.

  const url = new URL(req.url);
  const isAppShell = url.origin === self.location.origin;
  const isFirebaseSdk = FIREBASE_URLS.includes(req.url);
  if (!isAppShell && !isFirebaseSdk) return; // let Firestore's own network calls pass through untouched

  // Stale-while-revalidate: serve the cached copy instantly, refresh it in the
  // background, and fall back to cache (or a friendly offline response) if the
  // network is unavailable - this is what makes cold-start airplane mode work.
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((resp) => {
          if (resp && resp.status === 200) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, clone));
          }
          return resp;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
