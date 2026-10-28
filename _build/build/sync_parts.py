# -*- coding: utf-8 -*-
# Синхронизация канонических частей (style.css + header + ui.js) во все страницы сайта.
# Не трогает контент страниц, page-CSS и страничные скрипты.
import io
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(SITE, "_build", "build")
PARTS = os.path.join(SITE, "_build", "parts")
sys.path.insert(0, BUILD)
import build_all  # noqa: E402

rewrite_links = build_all.rewrite_links

STYLE = open(os.path.join(PARTS, "style.css"), encoding="utf-8").read()
FONTS = open(os.path.join(PARTS, "fonts.css"), encoding="utf-8").read()
HEADER = open(os.path.join(PARTS, "header.html"), encoding="utf-8").read()
UI_JS = open(os.path.join(PARTS, "ui.js"), encoding="utf-8").read()

PAGE_CSS_MARKER = "/* --- страничные стили --- */"
STYLE_RE = re.compile(r"(?s)<style>\n(.*?)</style>")
HEADER_RE = re.compile(r'(?s)<a class="skip-link".*?<div class="ruler" aria-hidden="true"></div>')
UI_MARKER = "// Общая логика интерфейса"

n_pages = 0
errors = []

for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, SITE).replace("\\", "/")
        prefix = "../" * rel.count("/")
        t = io.open(p, encoding="utf-8").read()

        if 'class="skip-link"' not in t:
            continue  # редирект-заглушки — пропускаем

        orig = t

        # --- 1. style ---
        m = STYLE_RE.search(t)
        if not m:
            errors.append(rel + ": no <style>")
            continue
        css_old = m.group(1)
        page_css = ""
        if PAGE_CSS_MARKER in css_old:
            page_css = PAGE_CSS_MARKER + css_old.split(PAGE_CSS_MARKER, 1)[1]
        css_new = (FONTS.replace("__PREFIX__", prefix) + "\n" + STYLE).rstrip("\n")
        if page_css:
            css_new += "\n" + page_css.rstrip("\n")
        css_new += "\n"
        t = t[:m.start(1)] + css_new + t[m.end(1):]

        # --- 2. header ---
        hm = HEADER_RE.search(t)
        if not hm:
            errors.append(rel + ": no header block")
            continue
        t = t[:hm.start()] + rewrite_links(HEADER, prefix).rstrip("\n") + "\n" + t[hm.end():].lstrip("\n")

        # --- 3. ui.js: первый <script> в body с маркером ---
        sm = re.search(r"(?s)<script>\n(.*?)</script>", t[hm.end():])
        # ищем именно скрипт с маркером (первый script после header)
        found = False
        for m2 in re.finditer(r"(?s)<script>\n(.*?)\n</script>", t):
            if UI_MARKER in m2.group(1):
                t = t[:m2.start(1)] + rewrite_links(UI_JS, prefix).rstrip("\n") + t[m2.end(1):]
                found = True
                break
        if not found:
            errors.append(rel + ": no ui.js block")
            continue

        if t != orig:
            io.open(p, "w", encoding="utf-8", newline="\n").write(t)
            n_pages += 1

print("synced pages:", n_pages)
if errors:
    print("ERRORS:")
    for e in errors:
        print("  -", e)
    raise SystemExit(1)

# самопроверка на одной странице каждой глубины
for probe in ("index.html", "ipoteka/index.html"):
    t = io.open(os.path.join(SITE, probe), encoding="utf-8").read()
    for token in ("nav-cat-btn", "nav-cat-panel", "closeNavCats"):
        assert token in t, probe + ": missing " + token
    for stale in ("mega-grid", "mega-cat", "mega-btn", "mega-panel", "closeMegaCats"):
        assert stale not in t, probe + ": stale " + stale
    assert 'href="calc-' not in t, probe + ": unrewritten link"
print("self-checks: ALL PASS")
