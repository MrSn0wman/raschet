# -*- coding: utf-8 -*-
# Замена футера во всех страницах сайта на новый (таксономия мега-меню).
# Ссылки из parts/footer.html (calc-*.html) конвертируются в ЧПУ с префиксом глубины.
import io
import os
import re
import sys

SITE = r"C:\Kimi\raschet"
sys.path.insert(0, r"C:\Kimi\raschet\_build\build")
import build_all  # noqa: E402  (импорт без запуска: main() под guard)

SLUG_MAP = build_all.LINK_MAP  # {'calc-mortgage.html': 'ipoteka', ..., 'calc-currency.html': 'konverter-valyut', ...}

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

footer_tpl = read(os.path.join(SITE, "_build", "parts", "footer.html"))

def footer_for(prefix):
    f = footer_tpl
    f = f.replace('href="index.html"', 'href="%s"' % ("./" if prefix == "" else "../"))
    for old in sorted(SLUG_MAP.keys(), key=len, reverse=True):
        f = f.replace('href="' + old + '"', 'href="%s%s/"' % (prefix, SLUG_MAP[old]))
    for st in ("about", "privacy", "advertising", "feedback"):
        f = f.replace('href="%s.html"' % st, 'href="%s%s/"' % (prefix, st))
    return f

FOOT_RE = re.compile(r"(?s)<footer class=\"site-footer\">.*?</footer>")

n = 0
miss = []
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        t = read(p)
        if '<footer class="site-footer">' not in t:
            continue
        rel = os.path.relpath(p, SITE).replace("\\", "/")
        prefix = "../" * rel.count("/")
        new_footer = footer_for(prefix)
        t2 = FOOT_RE.sub(lambda _: new_footer, t, count=1)
        if t2 != t:
            io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
            n += 1
        else:
            miss.append(rel)
print("footers replaced:", n, "| no-change:", miss[:5])
# проверка: ни один футер не должен содержать calc-*.html
bad = 0
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if fn.endswith(".html"):
            t = read(os.path.join(root, fn))
            fm = re.search(r"(?s)<footer class=\"site-footer\">.*?</footer>", t)
            if fm and "calc-" in fm.group(0):
                bad += 1
print("footers with leftover calc- links:", bad)
