// Rally Racing – Offline-Speicher. Bei jedem Update die Versionsnummer erhöhen.
const CACHE = 'rally-racing-v7';
const CORE = ['./', 'index.html', 'audi.bin', 'audi_d.png', 'lancer.bin', 'lancer_d.png', 'subaru.bin', 'subaru_d.png', 'celica.bin', 'celica_d.png', 'bmw.bin', 'bmw_d.png', 'fiat.bin', 'fiat_d.png', 'r5.bin', 'r5_d.png', 'delta.bin', 'delta_d.png', 'escort.bin', 'escort_d.png', 'rs200.bin', 'rs200_d.png', 'p959.bin', 'p959_d.png', 's4.bin', 's4_d.png', 'p205.bin', 'p205_d.png', 'stratos.bin', 'stratos_d.png', 'alpine.bin', 'alpine_d.png', 'cars_th.png', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Eigene Dateien: erst Netz (für Updates), sonst Cache; three.js und Schrift: erst Cache
  const own = u.origin === location.origin;
  if (own) e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); return r; }).catch(() => caches.match(e.request, { ignoreSearch: true })));
  else e.respondWith(caches.match(e.request).then(m => m || fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); } return r; })));
});
