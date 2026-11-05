# -*- coding: utf-8 -*-
"""Idempotent, privacy-safe PWA integration on the explicit --site tree.

Canonical analytics is assets/analytics.js: never replace it with an embedded
tracker. Hash only final public HTML/static assets, excluding sw.js and JSON.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path
from site_common import PARTS, html_files, read, site_parser, write
from integrate_rsya import privacy_loader, remove_ads, sensitive_routes

HEAD_SNIPPET = ('<link rel="manifest" href="{prefix}manifest.webmanifest">\n'
                '<meta name="theme-color" content="#0E7A4A">\n'
                '<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/icon-192.png">\n'
                '<link rel="apple-touch-icon" href="{prefix}assets/icon-192.png">\n')
SW_REGISTER = """<script>
if ('serviceWorker' in navigator){
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('%PREFIX%sw.js').catch(function(){});
  });
}
</script>
</body>"""

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

def write(p, text):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

# --- 1. копирование ассетов ---
os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
shutil.copy(os.path.join(PARTS, "manifest.webmanifest"), os.path.join(SITE, "manifest.webmanifest"))
for name in ("icon-192.png", "icon-512.png", "icon-maskable-512.png"):
    shutil.copy(os.path.join(ASSETS_SRC, name), os.path.join(SITE, "assets", name))
# vendor-библиотеки (qrcodejs — локально вместо CDN: офлайн и нет supply-chain риска)
vendor_dst = os.path.join(SITE, "assets", "vendor")
os.makedirs(vendor_dst, exist_ok=True)
for name in os.listdir(os.path.join(ASSETS_SRC, "vendor")):
    shutil.copy(os.path.join(ASSETS_SRC, "vendor", name), os.path.join(vendor_dst, name))
fonts_dst = os.path.join(SITE, "assets", "fonts")
os.makedirs(fonts_dst, exist_ok=True)
for name in os.listdir(os.path.join(ASSETS_SRC, "fonts")):
    shutil.copy(os.path.join(ASSETS_SRC, "fonts", name), os.path.join(fonts_dst, name))
print("assets copied")

# --- 2. список страниц и precache ---
import hashlib

def tree_hash():
    h = hashlib.sha1()
    for root, dirs, files in os.walk(SITE):
        dirs[:] = sorted(d for d in dirs if d not in ("_build", "backend", "_seo_tmp"))
        for fn in sorted(files):
            if fn.endswith((".html", ".js", ".css", ".webmanifest")):
                fp = os.path.join(root, fn)
                h.update(os.path.relpath(fp, SITE).replace("\\", "/").encode())
                with open(fp, "rb") as f:
                    h.update(f.read())
    return h.hexdigest()[:10]

html_files = []
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", "_seo_tmp")]
    for fn in files:
        if fn.endswith(".html"):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, SITE).replace("\\", "/")
            html_files.append(rel)

# precache: страницы + ассеты + служебные
precache = ["./", "./manifest.webmanifest"]
for rel in sorted(html_files):
    if rel == "index.html":
        continue  # уже есть как ./
    if rel.endswith("/index.html"):
        precache.append("./" + rel[: -len("/index.html")] + "/")
    else:
        precache.append("./" + rel)
for name in ("icon-192.png", "icon-512.png", "icon-maskable-512.png"):
    precache.append("./assets/" + name)
precache.append("./assets/analytics.js")
for name in sorted(os.listdir(fonts_dst)):
    precache.append("./assets/fonts/" + name)
for name in sorted(os.listdir(vendor_dst)):
    precache.append("./assets/vendor/" + name)

# QR-страница: CDN → локальная копия (любая глубина папки — переписываем с правильным prefix)
CDN_QR = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"
for rel in html_files:
    full = os.path.join(SITE, rel)
    text = read(full)
    if CDN_QR in text:
        prefix = "../" * rel.count("/")
        text = text.replace(CDN_QR, prefix + "assets/vendor/qrcode.min.js")
        write(full, text)
        print("CDN->local qrcode:", rel)

# nbsp перед «₽» в JS-строках результатов (чтобы «55 054 ₽» не рвалось)
nbsp_fixed = 0
for rel in html_files:
    full = os.path.join(SITE, rel)
    text = read(full)
    if "+ ' ₽'" in text:
        text = text.replace("+ ' ₽'", "+ '\\u00A0₽'")
        write(full, text)
        nbsp_fixed += 1
print("nbsp fix in", nbsp_fixed, "pages")

# --- 4. аналитика (Яндекс.Метрика — официальный сниппет, id в query) + .nojekyll ---
ANALYTICS_JS = """// Расчёт.net — аналитика. ID счётчиков зашиты здесь, больше ничего менять не надо.
// Яндекс.Метрика: https://metrika.yandex.ru → Счётчики → ID счётчика (число)
// GA4: https://analytics.google.com → Администратор → Потоки данных → G-XXXXXXX
var YM_ID = '113965438';   // Яндекс.Метрика, raschet.net
var GA_ID = '';   // например 'G-ABC123DEF4'
(function(){
  if (YM_ID){
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id='+encodeURIComponent(YM_ID), 'ym');
    ym(Number(YM_ID), 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:'dataLayer', referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
  }
  if (GA_ID){
    var s=document.createElement('script'); s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(GA_ID);
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){dataLayer.push(arguments)};
    gtag('js',new Date()); gtag('config',GA_ID);
  }
})();
"""

# No runtime cache writes. Only versioned, explicitly public files are precached;
# query/API requests and privacy-bearing responses never enter CacheStorage.
SW_TEMPLATE = r"""// Generated by integrate_pwa.py; deterministic public precache only.
const CACHE = 'raschet-%HASH%';
const PRECACHE = %PRECACHE%;
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
"""

def public_files(site):
    site = Path(site)
    for path in sorted(site.rglob('*')):
        if not path.is_file(): continue
        rel = path.relative_to(site).as_posix()
        if any(part in ('_build', 'backend', 'tests', 'scripts', '.git', '.github') or part.startswith('.') for part in path.relative_to(site).parts) or rel == 'sw.js' or rel.endswith('.json'):
            continue
        if path.suffix in ('.html', '.js', '.css', '.webmanifest', '.woff2', '.png', '.svg', '.ico', '.webp'):
            yield path

def tree_hash(site):
    digest = hashlib.sha256()
    for path in public_files(site):
        digest.update(path.relative_to(site).as_posix().encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
    return digest.hexdigest()[:20]

def process(site, parts=PARTS):
    from site_common import safe_destination
    site = safe_destination(site)
    site, parts = Path(site), Path(parts)
    manifest = json.loads(read(parts / 'manifest.webmanifest'))
    if manifest.get('start_url') not in ('./', '/') or manifest.get('scope') not in ('./', '/'):
        raise ValueError('Manifest must use root-relative scope/start without query/API')
    write(site / 'manifest.webmanifest', read(parts / 'manifest.webmanifest'))
    for name in ('analytics.js',):
        if not (site / 'assets' / name).is_file(): raise ValueError('Missing canonical asset: ' + name)
    privacy = parts / 'privacy.js'
    if not privacy.is_file(): raise ValueError('Missing canonical privacy policy')
    shutil.copyfile(privacy, site / 'assets' / 'privacy.js')
    sensitive = sensitive_routes(parts)
    for path in html_files(site):
        rel = path.relative_to(site).as_posix()
        text = read(path)
        if path.name.startswith(('google', 'yandex_')): continue
        # Redirects are minimal and must not gain analytics or SW registrations.
        if rel.startswith('calc-'): continue
        prefix = '../' * rel.count('/')
        text = privacy_loader(text, prefix)
        if rel.split('/')[0] in sensitive:
            text = remove_ads(text)
        elif 'assets/analytics.js' not in text:
            text = text.replace('</head>', '<script src="%sassets/analytics.js" defer></script>\n</head>' % prefix, 1)
        if 'rel="manifest"' not in text:
            text = text.replace('<meta name="viewport"', HEAD_SNIPPET.replace('{prefix}', prefix) + '<meta name="viewport"', 1)
        if 'navigator.serviceWorker.register' not in text:
            text = text.replace('</body>', SW_REGISTER.replace('%PREFIX%', prefix) + '</body>', 1)
        text = text.replace('https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js', prefix + 'assets/vendor/qrcode.min.js')
        text = text.replace("+ ' ₽'", "+ '\\u00A0₽'")
        if text != read(path): write(path, text)
    precache = []
    for path in public_files(site):
        rel = path.relative_to(site).as_posix()
        if rel.startswith('calc-') or path.name.startswith(('google', 'yandex_')): continue
        route = './' if rel == 'index.html' else './' + rel.removesuffix('index.html') if rel.endswith('/index.html') else './' + rel
        precache.append(route)
    precache.sort()
    sw = SW_TEMPLATE.replace('%HASH%', tree_hash(site)).replace('%PRECACHE%', json.dumps(precache, ensure_ascii=False, indent=2))
    write(site / 'sw.js', sw)
    print('PWA stable public precache:', len(precache))

if __name__ == '__main__':
    parser = site_parser(__doc__)
    parser.add_argument('--parts', type=Path, default=PARTS)
    args = parser.parse_args()
    process(args.site, args.parts)
