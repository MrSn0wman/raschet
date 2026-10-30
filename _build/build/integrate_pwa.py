# -*- coding: utf-8 -*-
# PWA-интеграция поверх собранного сайта C:\Kimi\raschet-site:
# 1) копирует manifest.webmanifest, иконки, шрифты;
# 2) генерирует sw.js с полным precache всех страниц и ассетов (полный офлайн);
# 3) в каждый HTML вставляет <link rel="manifest">, <meta name="theme-color">,
#    регистрацию service worker.
# Идемпотентен: повторный запуск не дублирует вставки.
import io
import os
import re
import shutil

SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARTS = os.path.join(SITE, "_build", "parts")
ASSETS_SRC = os.path.join(SITE, "_build", "assets")

HEAD_SNIPPET = (
    '<link rel="manifest" href="{prefix}manifest.webmanifest">\n'
    '<meta name="theme-color" content="#0E7A4A">\n'
    '<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/icon-192.png">\n'
    '<link rel="apple-touch-icon" href="{prefix}assets/icon-192.png">'
)

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
        dirs[:] = sorted(d for d in dirs if d not in ("_build", "backend"))
        for fn in sorted(files):
            if fn.endswith((".html", ".js", ".css", ".webmanifest")):
                fp = os.path.join(root, fn)
                h.update(os.path.relpath(fp, SITE).replace("\\", "/").encode())
                with open(fp, "rb") as f:
                    h.update(f.read())
    return h.hexdigest()[:10]

html_files = []
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets")]
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

# --- 4. аналитика (плейсхолдеры) + .nojekyll ---
ANALYTICS_JS = """// Расчёт.net — аналитика. Заполните ID и сохраните файл — больше ничего менять не надо.
// Яндекс.Метрика: https://metrika.yandex.ru → Счётчики → ID счётчика (число)
// GA4: https://analytics.google.com → Администратор → Потоки данных → G-XXXXXXX
var YM_ID = '';   // например '12345678'
var GA_ID = '';   // например 'G-ABC123DEF4'
(function(){
  if (YM_ID){
    (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,'script','https://mc.yandex.ru/metrika/tag.js','ym');
    ym(Number(YM_ID),'init',{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true});
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
write(os.path.join(SITE, "assets", "analytics.js"), ANALYTICS_JS)
write(os.path.join(SITE, ".nojekyll"), "")

inj2 = 0
for rel in html_files:
    full = os.path.join(SITE, rel)
    text = read(full)
    if 'assets/analytics.js' in text:
        continue
    prefix = "../" * rel.count("/")
    tag = '<script src="%sassets/analytics.js" defer></script>\n</head>' % prefix
    if "</head>" in text:
        text = text.replace("</head>", tag, 1)
        write(full, text)
        inj2 += 1
print("analytics injected:", inj2)

sw = """// Расчёт.net — service worker (полный офлайн).
// Генерируется integrate_pwa.py — не править вручную.
const CACHE = 'raschet-%s';
const PRECACHE = %s;

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
""" % (tree_hash() + "-" + str(len(precache)),
       "[\n  " + ",\n  ".join('"%s"' % p for p in precache) + "\n]")
write(os.path.join(SITE, "sw.js"), sw)
print("sw.js written:", len(precache), "precache entries")

# --- 3. инъекции в HTML ---
injected = 0
for rel in html_files:
    full = os.path.join(SITE, rel)
    text = read(full)
    depth = rel.count("/")
    prefix = "../" * depth
    changed = False
    if 'rel="manifest"' not in text:
        snippet = HEAD_SNIPPET.replace("{prefix}", prefix) + "\n"
        text = text.replace('<meta name="viewport"', snippet + '<meta name="viewport"', 1)
        changed = True
    if 'serviceWorker' not in text:
        text = text.replace("</body>", SW_REGISTER.replace("%PREFIX%", prefix) + "\n", 1)
        changed = True
    if changed:
        write(full, text)
        injected += 1
print("html injected:", injected, "of", len(html_files))
print("PWA DONE")
