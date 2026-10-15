# -*- coding: utf-8 -*-
import io

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

for p in [r"C:\Kimi\raschet-site\index.html",
          r"C:\Kimi\raschet-site\ipoteka\index.html",
          r"C:\Kimi\raschet-site\calc-mortgage.html",
          r"C:\Kimi\raschet-site\404.html"]:
    t = read(p)
    name = p.split("raschet-site")[-1]
    print(name,
          "| manifest:", t.count('rel="manifest"'),
          "| sw:", t.count("serviceWorker"),
          "| analytics:", t.count("analytics.js"),
          "| nbsp-ruble:", t.count("₽"))
