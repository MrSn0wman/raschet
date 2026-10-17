# -*- coding: utf-8 -*-
# Тире в легенде графика не должно уезжать на свою строку: « — <b» → «&nbsp;— <b»
import io
import os

SITE = r"C:\Kimi\raschet"
n = 0
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        t = io.open(p, encoding="utf-8").read()
        if " — <b id=" in t and "-legend-" in t:
            t2 = t.replace(" — <b id=", "&nbsp;— <b id=")
            if t2 != t:
                io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
                n += 1
print("legend nbsp patched:", n)
