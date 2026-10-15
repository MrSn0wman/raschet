# -*- coding: utf-8 -*-
# Вставка meta CSP во все страницы готового сайта (идемпотентно).
import io
import os

SITE = r"C:\Kimi\raschet"
CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; '
       "script-src 'self' 'unsafe-inline' https://mc.yandex.ru https://www.googletagmanager.com; "
       "style-src 'self' 'unsafe-inline'; img-src 'self' data: https://mc.yandex.ru; "
       "font-src 'self'; connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
       "https://www.googletagmanager.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'\">")
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

n = 0
skipped = 0
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        t = io.open(p, encoding="utf-8").read()
        if "Content-Security-Policy" in t:
            skipped += 1
            continue
        if VIEWPORT in t:
            t = t.replace(VIEWPORT, VIEWPORT + "\n" + CSP, 1)
            io.open(p, "w", encoding="utf-8", newline="\n").write(t)
            n += 1
        else:
            print("NO VIEWPORT:", p)
print("CSP inserted:", n, "| already had:", skipped)
