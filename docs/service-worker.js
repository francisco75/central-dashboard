// v3 — self-unregister to clear bad v1 cache, then re-register as clean SW
const CACHE_NAME = 'central-r4-v3';

self.addEventListener('install', e => {
  // Clear ALL old caches
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(self.clients.claim());
});

// Never cache HTML — always fetch from network
self.addEventListener('fetch', e => {
  e.respondWith(fetch(e.request));
});
