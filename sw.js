// Rally Racing – Offline-Speicher. Bei jedem Update die Versionsnummer erhöhen.
const CACHE = 'rally-racing-v14-5';
const CARS = ['audi', 'lancer', 'subaru', 'celica', 'bmw', 'fiat', 'r5', 'delta', 'escort', 'rs200', 'p959', 's4', 'p205', 'stratos', 'alpine', 'fulvia', 'mini'];
// Beifahrer-Stimme (Florian), kurze Schnipsel in zwei Betonungen (Satzmitte _m / Satzende)
const VOICE = ['ach', 'd100', 'd100_m', 'd150', 'd150_m', 'd200', 'd200_m', 'd250', 'd250_m', 'd300', 'd300_m', 'd350', 'd350_m', 'd400', 'd400_m', 'd50', 'd50_m', 'eis', 'eis_m', 'eng', 'eng_m', 'go', 'hn', 'hn_m', 'in', 'kuppe', 'kuppe_m', 'l1', 'l1_m', 'l2', 'l2_m', 'l3', 'l3_m', 'l4', 'l4_m', 'l5', 'l5_m', 'l6', 'l6_m', 'lang', 'lang_m', 'leicht', 'leicht_m', 'lg', 'lg_m', 'mittel', 'mittel_m', 'neunzig', 'neunzig_m', 'ns', 'ns_m', 'of', 'of_m', 'r1', 'r1_m', 'r2', 'r2_m', 'r3', 'r3_m', 'r4', 'r4_m', 'r5', 'r5_m', 'r6', 'r6_m', 'ready', 'sprung', 'sprung_m', 'ziel', 'zs', 'zs_m', 'zz', 'zz_m'];
const CORE = ['./', 'index.html', 'img/cars_th.png', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'audio/Titel.mp3', 'img/cls_klassik.jpg', 'img/cls_grpa.jpg', 'img/cls_wrc.jpg', 'img/cls_grpb.jpg', 'img/career_hero.jpg', ...CARS.flatMap(c => ['cars/' + c + '.bin', 'cars/' + c + '_d.png']), ...VOICE.map(k => 'voice/' + k + '.mp3')];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(f => c.add(new Request(f, { cache: 'reload' })).catch(() => { })))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Musik: aus dem Cache, sonst einmal komplett laden und ablegen (keine Teil-Antworten speichern)
  if (u.pathname.endsWith('.mp3')) {
    e.respondWith(caches.match(u.href, { ignoreSearch: true }).then(m => m || fetch(u.href).then(r => { if (r.ok && r.status === 200) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(u.href, c)); } return r; })));
    return;
  }
  // Liste des Musik-Ordners immer frisch holen (offline: letzte bekannte Antwort)
  if (u.hostname === 'api.github.com') { e.respondWith(fetch(e.request).catch(() => caches.match(e.request))); return; }
  const own = u.origin === location.origin;
  // Seite selbst immer frisch vom Server prüfen (kein veralteter Browser-Cache), offline aus dem Speicher
  const page = e.request.mode === 'navigate' || u.pathname.endsWith('.html') || u.pathname.endsWith('/');
  if (own) e.respondWith((page ? fetch(u.href, { cache: 'no-cache', credentials: 'same-origin' }) : fetch(e.request)).then(r => { if (r.ok && r.status === 200) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); } return r; }).catch(() => caches.match(e.request, { ignoreSearch: true })));
  else e.respondWith(caches.match(e.request).then(m => m || fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); } return r; })));
});
