/**
 * Netra - Progressive Web App Service Worker
 * Version: 1.0.0
 *
 * Caches the core application shell (HTML, CSS tokens, vendor Three.js, scripts, icons)
 * and serves the offline fallback page when no internet connection is detected.
 */

const CACHE_NAME = 'netra-shell-v1';
const OFFLINE_URL = '/offline/';

const APP_SHELL = [
  '/',
  '/offline/',
  '/manifest.webmanifest',
  '/static/css/netra.css',
  '/static/vendor/three.min.js',
  '/static/js/home.js',
  '/static/js/hero3d.js',
  '/static/icons/icon.svg',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        APP_SHELL.map((url) => {
          return fetch(url).then((response) => {
            if (response.ok) {
              return cache.put(url, response);
            }
          }).catch((err) => {
            console.warn(`[Netra SW] Failed to pre-cache ${url}:`, err);
          });
        })
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET requests or Django admin
  if (request.method !== 'GET' || url.pathname.startsWith('/admin/')) {
    return;
  }

  // Navigation requests (HTML documents) -> Network first, fall back to cache or offline page
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(async () => {
          const cachedMatch = await caches.match(request);
          if (cachedMatch) return cachedMatch;

          const offlineMatch = await caches.match(OFFLINE_URL);
          if (offlineMatch) return offlineMatch;

          return new Response(
            `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Netra - Offline</title></head><body style="background:#f5efe6;font-family:sans-serif;padding:40px;text-align:center;"><h1>Netra is offline</h1><p>Check your connection to reload the page.</p></body></html>`,
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        })
    );
    return;
  }

  // Static Assets -> If versioned (?v=), fetch network first to ensure fresh styles/scripts
  if (url.pathname.startsWith('/static/')) {
    if (url.search) {
      event.respondWith(
        fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.ok) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        }).catch(() => caches.match(request))
      );
      return;
    }

    event.respondWith(
      caches.match(request).then((cached) => {
        const fetchPromise = fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.ok) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        }).catch(() => {/* offline */});

        return cached || fetchPromise;
      })
    );
    return;
  }

  // Fallback default
  event.respondWith(
    caches.match(request).then((cached) => {
      return cached || fetch(request).catch(() => {});
    })
  );
});
