/* Service worker de MA|OG — solo cachea el "cascarón" de la app (el
   index.html, el manifest, los íconos) para que abra aunque se vaya
   el internet. NO toca nada que vaya a Supabase, Resend, Google
   Fonts o el CDN de Excel — esas llamadas van a otro dominio y se
   dejan pasar de largo, sin caché, para nunca mostrar datos viejos
   como si fueran de ahora.

   Estrategia: "cache primero, y de una vez trae lo nuevo por detrás"
   — abre rápido incluso con mala señal, y la próxima vez que se abra
   ya está actualizado. Sube el número de CACHE si algún día hay que
   forzar que todo el mundo baje una versión nueva del cascarón. */
const CACHE = 'maog-shell-v3';
const SHELL = [
  '/', '/index.html', '/manifest.json',
  '/icons/icon-192.png', '/icons/icon-512.png',
  '/icons/icon-gasto-96.png', '/icons/icon-gasto-192.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
      .catch(() => {}) // sin internet en la primerísima visita: no pasa nada, se reintenta después
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== location.origin) return; // Supabase, Resend, fuentes, CDN de Excel: intactos

  event.respondWith(
    caches.match(event.request).then(cached => {
      const fresco = fetch(event.request).then(res => {
        if (res && res.ok) caches.open(CACHE).then(c => c.put(event.request, res.clone()));
        return res;
      }).catch(() => cached);
      return cached || fresco;
    })
  );
});
