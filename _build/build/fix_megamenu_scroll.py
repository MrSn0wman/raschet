# -*- coding: utf-8 -*-
# Фикс прокрутки мега-меню во всех страницах сайта (style.css инлайнен в каждую).
import io
import os

SITE = r"C:\Kimi\raschet"
OLD = """.mega-panel{
  position:absolute; left:0; right:0; top:100%;
  background:var(--surface); border-bottom:1px solid var(--line);
  box-shadow:var(--shadow-pop);
  padding:26px 0 30px;
  z-index:105;
}"""
NEW = """.mega-panel{
  position:absolute; left:0; right:0; top:100%;
  background:var(--surface); border-bottom:1px solid var(--line);
  box-shadow:var(--shadow-pop);
  padding:26px 0 30px;
  z-index:105;
  max-height:calc(100vh - 66px);
  overflow-y:auto;
  overscroll-behavior:contain;
}"""

n = 0
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
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
        else:
            if "mega-panel" in t:
                print("MISS:", p)
print("patched:", n)
