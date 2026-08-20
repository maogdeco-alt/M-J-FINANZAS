// Service Worker de Radicados Semanales — existe SOLO para dos cosas:
// 1) Que Chrome/Edge/Android ofrezcan "Instalar app" (exigen un Service Worker registrado).
// 2) Que si la abres sin señal, cargue igual (con la última versión que alcanzó a guardar) en vez
//    de mostrar la pantalla de error del navegador.
//
// Estrategia deliberadamente "primero la red" para todo lo que sirve este mismo sitio: SIEMPRE
// intenta traer la versión más nueva de internet primero, y solo usa la copia guardada si de
// verdad no hay conexión. Así nunca te quedas viendo una versión vieja de la app por un problema
// clásico de los Service Workers mal hechos (quedarse "pegado" en una copia cacheada y no dejar
// pasar las actualizaciones). Las llamadas a Supabase (otro dominio) NUNCA pasan por aquí — se
// dejan pasar de largo, intactas, para no arriesgar en nada la sincronización de tus radicados.

const CACHE_NAME = "radicados-shell-v1";
const SHELL_FILES = [
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", function(event){
  self.skipWaiting(); // la version nueva del SW toma control de inmediato, sin esperar a cerrar todas las pestañas
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){ return cache.addAll(SHELL_FILES); }).catch(function(){})
  );
});

self.addEventListener("activate", function(event){
  event.waitUntil(
    caches.keys().then(function(names){
      return Promise.all(names.filter(function(n){ return n !== CACHE_NAME; }).map(function(n){ return caches.delete(n); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(event){
  var req = event.request;
  if(req.method !== "GET") return; // nunca intervenir POST/PATCH -- ahí van los guardados hacia Supabase
  var url = new URL(req.url);
  if(url.origin !== self.location.origin) return; // Supabase y cualquier otro dominio: se deja pasar de largo, sin tocar

  event.respondWith(
    fetch(req).then(function(res){
      var copy = res.clone();
      caches.open(CACHE_NAME).then(function(cache){ cache.put(req, copy); }).catch(function(){});
      return res;
    }).catch(function(){
      return caches.match(req).then(function(cached){ return cached || caches.match("./index.html"); });
    })
  );
});
