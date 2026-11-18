// PanGeo: l'app si apre anche senza rete o con il programma spento,
// mostrando l'ultima versione salvata; quando la rete c'è, prende i dati nuovi.
const CACHE = 'pangeo-2.7';
const BASE = ['./', 'index.html', 'manifest.webmanifest', 'icona-192.png', 'icona-512.png'];
const chiave = u => u.origin + u.pathname;
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    e.respondWith(fetch(r).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(CACHE).then(k => k.put(chiave(u), c)); }
      return res;
    }).catch(() => caches.match(chiave(u)).then(m => m || caches.match(new URL('./', location.href).href))));
  } else if (u.hostname === 'cdn.jsdelivr.net') {
    e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => {
      const c = res.clone(); caches.open(CACHE).then(k => k.put(r, c)); return res;
    })));
  }
});
