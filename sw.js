// Rally Racing – Offline-Speicher. Bei jedem Update die Versionsnummer erhöhen.
const CACHE = 'rally-racing-v13-1';
const CARS = ['audi', 'lancer', 'subaru', 'celica', 'bmw', 'fiat', 'r5', 'delta', 'escort', 'rs200', 'p959', 's4', 'p205', 'stratos', 'alpine', 'fulvia', 'mini'];
const CORE = ['./', 'index.html', 'cars_th.png', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'nebulite-overdrive.mp3', 'cls_klassik.jpg', 'cls_grpa.jpg', 'cls_wrc.jpg', 'cls_grpb.jpg', 'career_hero.jpg', ...CARS.flatMap(c => [c + '.bin', c + '_d.png'])];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE.map(f => new Request(f, { cache: 'reload' })))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Musik: aus dem Cache, sonst einmal komplett laden und ablegen (keine Teil-Antworten speichern)
  if (u.pathname.endsWith('.mp3')) {
    e.respondWith(caches.match(u.href, { ignoreSearch: true }).then(m => m || fetch(u.href).then(r => { if (r.ok && r.status === 200) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(u.href, c)); } return r; })));
    return;
  }
  const own = u.origin === location.origin;
  // Seite selbst immer frisch vom Server prüfen (kein veralteter Browser-Cache), offline aus dem Speicher
  const page = e.request.mode === 'navigate' || u.pathname.endsWith('.html') || u.pathname.endsWith('/');
  if (own) e.respondWith((page ? fetch(u.href, { cache: 'no-cache', credentials: 'same-origin' }) : fetch(e.request)).then(r => { if (r.ok && r.status === 200) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); } return r; }).catch(() => caches.match(e.request, { ignoreSearch: true })));
  else e.respondWith(caches.match(e.request).then(m => m || fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); } return r; })));
});
