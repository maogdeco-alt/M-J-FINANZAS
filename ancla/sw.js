const CACHE = 'ancla-v2';
const ARCHIVOS = ['./', './index.html', './manifest.json', './icon.svg'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ARCHIVOS); }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    }).then(function () {
      return self.clients.claim();
    }).then(function () {
      // Si esta activación viene de una versión vieja que dejó una pestaña
      // abierta con contenido atascado, recárgala sola — nadie debería tener
      // que darse cuenta a mano de que había una actualización esperando.
      return self.clients.matchAll({ type: 'window' });
    }).then(function (clientes) {
      clientes.forEach(function (c) { c.navigate(c.url); });
    })
  );
});

// Red primero, siempre: mientras haya internet, esto nunca vuelve a servir una
// versión vieja atascada en caché. El caché solo entra a jugar como respaldo
// si el fetch falla de verdad (sin conexión), y de paso se refresca con lo
// último que sí llegó a bajar.
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(function (resp) {
      var copia = resp.clone();
      caches.open(CACHE).then(function (c) { c.put(e.request, copia); });
      return resp;
    }).catch(function () {
      return caches.match(e.request).then(function (r) { return r || caches.match('./index.html'); });
    })
  );
});
