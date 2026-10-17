# -*- coding: utf-8 -*-
# «Сложный процент» → Финансы в источниках (генераторы), чтобы пересборка не вернула.
import io

for path in [r"C:\Kimi\raschet\_build\build\build_all.py",
             r"C:\Kimi\raschet\_build\build\build_index.py"]:
    t = io.open(path, encoding="utf-8").read()
    ok = 0
    old_fin = '"calc-iis.html","calc-currency.html"'
    new_fin = '"calc-iis.html","calc-currency.html","calc-compound-interest.html"'
    if old_fin in t:
        t = t.replace(old_fin, new_fin); ok += 1
    old_misc = ',"calc-compound-interest.html",'
    if old_misc in t:
        t = t.replace(old_misc, ",", 1); ok += 1
    old_lede = "Единицы, сложный процент, скидки, чаевые."
    if old_lede in t:
        t = t.replace(old_lede, "Единицы, скидки, чаевые."); ok += 1
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    print(path.split("\\")[-1], "patches:", ok)
