// Расчёт.рф — service worker (полный офлайн).
// Генерируется integrate_pwa.py — не править вручную.
const CACHE = 'raschet-3598b47be0-162';
const PRECACHE = [
  "./",
  "./manifest.webmanifest",
  "./404.html",
  "./about/",
  "./advertising/",
  "./avtokredit/",
  "./bolnichnyy/",
  "./calc-age.html",
  "./calc-amount-in-words.html",
  "./calc-area.html",
  "./calc-art395.html",
  "./calc-bmi.html",
  "./calc-car-loan.html",
  "./calc-compare-lists.html",
  "./calc-compound-interest.html",
  "./calc-credit.html",
  "./calc-customs-clearance.html",
  "./calc-days.html",
  "./calc-deposit.html",
  "./calc-discount.html",
  "./calc-ev-charging.html",
  "./calc-factorization.html",
  "./calc-fractions.html",
  "./calc-fuel.html",
  "./calc-gcd.html",
  "./calc-iis.html",
  "./calc-insurance-contributions.html",
  "./calc-lcm.html",
  "./calc-loan-interest.html",
  "./calc-maternal-capital-shares.html",
  "./calc-maternity-leave.html",
  "./calc-microloan.html",
  "./calc-mortgage-early.html",
  "./calc-mortgage.html",
  "./calc-ndfl.html",
  "./calc-number-base.html",
  "./calc-osago.html",
  "./calc-password-generator.html",
  "./calc-penalty-contract.html",
  "./calc-penalty-ddu.html",
  "./calc-penalty-tax.html",
  "./calc-pension.html",
  "./calc-percent.html",
  "./calc-power.html",
  "./calc-promo-generator.html",
  "./calc-property-sale-tax.html",
  "./calc-qr-generator.html",
  "./calc-random-number.html",
  "./calc-random-pick.html",
  "./calc-recycling-fee.html",
  "./calc-refinancing.html",
  "./calc-samozanyaty.html",
  "./calc-shares-apartment.html",
  "./calc-shuffle-list.html",
  "./calc-sick-leave.html",
  "./calc-split-groups.html",
  "./calc-tax-deduction.html",
  "./calc-timezone.html",
  "./calc-tip.html",
  "./calc-transport-tax.html",
  "./calc-unit-converter.html",
  "./calc-vacation-days.html",
  "./calc-vacation-pay.html",
  "./calc-vat.html",
  "./calc-volume.html",
  "./calc-weight.html",
  "./calc-work-experience.html",
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
  "./idealnyy-ves/",
  "./iis/",
  "./imt/",
  "./ipoteka/",
  "./konverter-edinic/",
  "./konverter-valyut/",
  "./kredit/",
  "./lorem-ipsum/",
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
  "./zaryadka-elektromobilya/",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png",
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
  "./assets/vendor/qrcode.min.js"
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return; // API, CDN — мимо кэша
  e.respondWith(
    caches.match(e.request).then((hit) => {
      if (hit) return hit;
      return fetch(e.request).then((resp) => {
        if (resp.ok){
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return resp;
      }).catch(() => {
        if (e.request.mode === 'navigate') return caches.match('./');
        throw new Error('offline');
      });
    })
  );
});
