# -*- coding: utf-8 -*-
# Разовый патч 28.10.2026:
# 1) новый init-скрипт темы (с theme-color) во все 79 страниц
# 2) CSP meta в 60 редирект-заглушек calc-*.html
import io
import os
import sys

SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OLD_INIT = '<script>(function(){try{var t=localStorage.getItem(\'raschet-theme\');if(t!==\'light\'&&t!==\'dark\'){t=window.matchMedia(\'(prefers-color-scheme: dark)\').matches?\'dark\':\'light\'}document.documentElement.setAttribute(\'data-theme\',t)}catch(e){document.documentElement.setAttribute(\'data-theme\',\'light\')}})();</script>'
NEW_INIT = '<script>(function(){try{var t=localStorage.getItem(\'raschet-theme\');if(t!==\'light\'&&t!==\'dark\'){t=window.matchMedia(\'(prefers-color-scheme: dark)\').matches?\'dark\':\'light\'}document.documentElement.setAttribute(\'data-theme\',t);var m=document.querySelector(\'meta[name="theme-color"]\');if(!m){m=document.createElement(\'meta\');m.setAttribute(\'name\',\'theme-color\');document.head.appendChild(m)}m.setAttribute(\'content\',t===\'dark\'?\'#101613\':\'#0E7A4A\')}catch(e){document.documentElement.setAttribute(\'data-theme\',\'light\')}})();</script>'

CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; '
       "script-src 'self' 'unsafe-inline' https://mc.yandex.ru https://www.googletagmanager.com; "
       "style-src 'self' 'unsafe-inline'; img-src 'self' data: https://mc.yandex.ru; font-src 'self'; "
       "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com https://www.googletagmanager.com; "
       "frame-ancestors 'none'; base-uri 'self'; form-action 'self'\">")

n_init = 0
n_csp = 0
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", ".git")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        t = io.open(p, encoding="utf-8").read()
        orig = t
        if OLD_INIT in t:
            assert t.count(OLD_INIT) == 1, p
            t = t.replace(OLD_INIT, NEW_INIT)
            n_init += 1
        if fn.startswith("calc-") and 'http-equiv="refresh"' in t and 'Content-Security-Policy' not in t:
            assert '<meta charset="UTF-8">' in t, p
            t = t.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n' + CSP, 1)
            n_csp += 1
        if t != orig:
            io.open(p, "w", encoding="utf-8", newline="\n").write(t)

print("init-скрипт заменён в %d страницах (ожидалось 79)" % n_init)
print("CSP добавлен в %d заглушек (ожидалось 60)" % n_csp)
if n_init != 79 or n_csp != 60:
    sys.exit(1)
print("OK")
