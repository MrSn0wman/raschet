# -*- coding: utf-8 -*-
# Скачивает woff2 для Inter / Fraunces / IBM Plex Mono с Google Fonts
# и генерирует fonts.css с @font-face на локальные файлы.
# Запуск: python fetch_fonts.py
import io
import os
import re
import urllib.request

OUT_DIR = r"C:\Kimi\raschet-redesign\assets\fonts"
CSS_OUT = r"C:\Kimi\raschet-redesign\parts\fonts.css"

FAMILIES = [
    ("Inter", "family=Inter:wght@400;500;600;700"),
    ("Fraunces", "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600"),
    ("IBM Plex Mono", "family=IBM+Plex+Mono:wght@400;500;600"),
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

os.makedirs(OUT_DIR, exist_ok=True)

css_out = []
for family, query in FAMILIES:
    url = "https://fonts.googleapis.com/css2?" + query + "&display=swap"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        css = r.read().decode("utf-8")
    # блоки @font-face
    blocks = re.findall(r"@font-face\s*\{[^}]*\}", css)
    # оставляем только latin (unicode-range без кириллицы нас не устроит — сайт русский!
    # Google режет на subsets: берём latin + cyrillic)
    wanted = []
    for b in blocks:
        if "U+0460-052F" in b or "U+0400-04FF" in b or "U+0400-045F" in b:  # cyrillic / cyrillic-ext
            wanted.append(b)
        elif "unicode-range" not in b:
            wanted.append(b)
        elif re.search(r"U\+0000-00FF", b):  # latin
            wanted.append(b)
    if not wanted:
        wanted = blocks
    seen = set()
    for b in wanted:
        fam = re.search(r"font-family:\s*'([^']+)'", b).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", b).group(1)
        style = re.search(r"font-style:\s*(\w+)", b).group(1)
        src = re.search(r"url\((https://[^)]+\.woff2)\)", b)
        if not src:
            continue
        subset = "cyrillic" if ("U+0400" in b or "U+0460" in b) else "latin"
        fname = "%s-%s-%s.woff2" % (fam.replace(" ", ""), weight, subset)
        key = (fam, weight, subset)
        if key in seen:
            continue
        seen.add(key)
        fpath = os.path.join(OUT_DIR, fname)
        if not os.path.exists(fpath):
            req2 = urllib.request.Request(src.group(1), headers={"User-Agent": UA})
            with urllib.request.urlopen(req2, timeout=60) as r2:
                data = r2.read()
            with open(fpath, "wb") as f:
                f.write(data)
            print("download:", fname, len(data))
        css_out.append(
            "@font-face{\n"
            "  font-family:'%s';\n"
            "  font-style:%s;\n"
            "  font-weight:%s;\n"
            "  font-display:swap;\n"
            "  src:url('__PREFIX__assets/fonts/%s') format('woff2');\n"
            "}" % (fam, style, weight, fname)
        )

with io.open(CSS_OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("/* Локальные шрифты (self-hosted, офлайн-PWA). __PREFIX__ заменяется генератором. */\n")
    f.write("\n".join(css_out))
    f.write("\n")

print("DONE:", len(css_out), "@font-face rules ->", CSS_OUT)
print("fonts dir:", len(os.listdir(OUT_DIR)), "files")
