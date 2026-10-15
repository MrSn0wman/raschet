# -*- coding: utf-8 -*-
# Синхронизация правки ui.js (проверка href в «Популярном») во все собранные страницы.
# ui.js инлайнен в каждую страницу — заменяем фрагмент по точному тексту.
import io
import os

SITE = r"C:\Kimi\raschet"
OLD = """          data.items.forEach((item, idx) => {
            const a = document.createElement('a');
            a.className = 'pop-item';
            a.href = item.href;"""
NEW = """          data.items.forEach((item, idx) => {
            // href принимаем только относительный (защита от javascript:-URL при компрометации API)
            if (!item || typeof item.href !== 'string' || !/^[a-z0-9][a-z0-9\\-\\/\\.]*$/i.test(item.href)) return;
            const a = document.createElement('a');
            a.className = 'pop-item';
            a.href = item.href;"""

n = 0
miss = []
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        t = io.open(p, encoding="utf-8").read()
        if NEW in t:
            continue
        if OLD in t:
            t = t.replace(OLD, NEW, 1)
            io.open(p, "w", encoding="utf-8", newline="\n").write(t)
            n += 1
        elif "popStrip" in t or "popular-strip" in t:
            miss.append(p)
print("patched:", n, "| miss:", miss)
