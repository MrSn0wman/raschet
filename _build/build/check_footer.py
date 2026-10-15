# -*- coding: utf-8 -*-
import io
import re

t = io.open(r"C:\Kimi\raschet\ipoteka\index.html", encoding="utf-8").read()
m = re.search(r'(?s)<footer class="site-footer">.*?</footer>', t)
f = m.group(0)
i = f.find("calc-")
print("idx:", i)
if i >= 0:
    print(repr(f[max(0, i - 60): i + 60]))
