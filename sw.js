// Расчёт.net — service worker (полный офлайн).
// Генерируется integrate_pwa.py — не править вручную.
const CACHE = 'raschet-bdc8db7d7b-164';
const PRECACHE = [
  "./",
  "./404.html",
  "./about/",
  "./advertising/",
  "./assets/analytics.js",
  "./assets/fonts/Fraunces-400-latin.woff2",
  "./assets/fonts/Fraunces-500-latin.woff2",
  "./assets/fonts/Fraunces-600-latin.woff2",
  "./assets/fonts/IBMPlexMono-400-cyrillic.woff2",
  "./assets/fonts/IBMPlexMono-400-latin.woff2",
  "./assets/fonts/IBMPlexMono-500-cyrillic.woff2",
  "./assets/fonts/IBMPlexMono-500-latin.woff2",
  "./assets/fonts/IBMPlexMono-600-cyrillic.woff2",
  "./assets/fonts/IBMPlexMono-600-latin.woff2",
  "./assets/fonts/Inter-400-cyrillic.woff2",
  "./assets/fonts/Inter-400-latin.woff2",
  "./assets/fonts/Inter-500-cyrillic.woff2",
  "./assets/fonts/Inter-500-latin.woff2",
  "./assets/fonts/Inter-600-cyrillic.woff2",
  "./assets/fonts/Inter-600-latin.woff2",
  "./assets/fonts/Inter-700-cyrillic.woff2",
  "./assets/fonts/Inter-700-latin.woff2",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png",
  "./assets/og-cover.png",
  "./assets/privacy.js",
  "./assets/vendor/qrcode.min.js",
  "./avtokredit/",
  "./bolnichnyy/",
  "./chaevye/",
  "./chasovye-poyasa/",
  "./dekretnye/",
  "./dni/",
  "./doli-po-materinskomu-kapitalu/",
  "./doli-v-kvartire/",
  "./dosrochnoe-pogashenie/",
  "./drobi/",
  "./feedback/",
  "./generator-nikneimov/",
  "./generator-paroley/",
  "./generator-promokodov/",
  "./google0c4ac994cf6febfa.html",
  "./idealnyy-ves/",
  "./iis/",
  "./imt/",
  "./ipoteka/",
  "./konverter-edinic/",
  "./konverter-valyut/",
  "./kredit/",
  "./lorem-ipsum/",
  "./manifest.webmanifest",
  "./mikrozaim/",
  "./nalog-s-prodazhi-kvartiry/",
  "./nalog-samozanyatyh/",
  "./nalogovyy-vychet-kvartira/",
  "./ndfl/",
  "./nds/",
  "./neustoika-po-ddu/",
  "./neustoika-po-dogovoru/",
  "./nod/",
  "./nok/",
  "./obem/",
  "./obratnyy-otschet/",
  "./osago/",
  "./otpusknye-dni/",
  "./otpusknye/",
  "./peni-po-nalogam/",
  "./pensiya/",
  "./peremeshat-spisok/",
  "./ploshad/",
  "./privacy/",
  "./procenty-395-gk/",
  "./procenty-po-zaimu/",
  "./procenty/",
  "./proverka-inn/",
  "./proverka-nomera-karty/",
  "./proverka-snils/",
  "./qr-generator/",
  "./rabochie-dni/",
  "./rashod-topliva/",
  "./rastamozhka/",
  "./razdelit-na-gruppy/",
  "./razlozhenie-na-mnozhiteli/",
  "./refinansirovanie/",
  "./schetchik-slov/",
  "./sistemy-schisleniya/",
  "./skidki/",
  "./slozhnyy-procent/",
  "./sluchaynye-chisla/",
  "./sluchaynyy-vybor/",
  "./sravnenie-spiskov/",
  "./stepeni/",
  "./strahovye-vznosy-ip/",
  "./summa-propisyu/",
  "./transliteraciya/",
  "./transportnyy-nalog/",
  "./trudovoy-stazh/",
  "./udalenie-dubley-strok/",
  "./unix-vremya/",
  "./utilsbor/",
  "./uuid-generator/",
  "./vklad/",
  "./vozrast/",
  "./zaryadka-elektromobilya/"
];
const ALLOWED = new Set(PRECACHE.map(p => new URL(p, self.registration.scope).pathname));
for (const pathname of [...ALLOWED]) if (pathname.endsWith('/')) ALLOWED.add(pathname + 'index.html');
function cacheURL(url){
  const key = new URL(url.href);
  if (key.pathname.endsWith('/index.html')) key.pathname = key.pathname.slice(0, -10);
  return key.href;
}
function publicResponse(response){
  const cc = response.headers.get('cache-control') || '';
  return response.ok && !response.redirected && response.type !== 'opaque' &&
    !/private|no-store|no-cache/i.test(cc) &&
    !(response.headers.get('vary') || '').includes('*') &&
    !response.headers.has('set-cookie');
}
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(async cache => {
    for (const path of PRECACHE){
      const request = new Request(new URL(path, self.registration.scope), {credentials:'omit', cache:'reload'});
      const response = await fetch(request);
      if (!publicResponse(response)) throw new Error('Non-public precache response');
      await cache.put(request, response);
    }
  }).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('raschet-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || url.search ||
      /(?:^|\/)api(?:\/|$)/i.test(url.pathname) || !ALLOWED.has(url.pathname) ||
      e.request.headers.has('authorization') || e.request.cache === 'no-store') return;
  if (e.request.mode === 'navigate'){
    e.respondWith(fetch(e.request).catch(() => caches.open(CACHE).then(c => c.match(cacheURL(url))).then(hit => hit || Promise.reject(new Error('offline')))));
    return;
  }
  e.respondWith(caches.open(CACHE).then(c => c.match(cacheURL(url))).then(hit => hit || fetch(e.request)));
});
