# -*- coding: utf-8 -*-
import io

JOBS = {
    r"C:\Kimi\raschet\_build\build\build_all.py": [
        ('OLD = r"C:\\Kimi\\raschet"', 'OLD = r"C:\\Kimi\\raschet-old"'),
        ('PARTS = r"C:\\Kimi\\raschet-redesign\\parts"', 'PARTS = r"C:\\Kimi\\raschet\\_build\\parts"'),
        ('TOOLS_DIR = r"C:\\Kimi\\raschet-redesign\\build\\tools"', 'TOOLS_DIR = r"C:\\Kimi\\raschet\\_build\\build\\tools"'),
        ('REPORT_PATH = r"C:\\Kimi\\raschet-redesign\\build\\build_report.txt"', 'REPORT_PATH = r"C:\\Kimi\\raschet\\_build\\build\\build_report.txt"'),
    ],
    r"C:\Kimi\raschet\_build\build\integrate_pwa.py": [
        ('SITE = r"C:\\Kimi\\raschet-site"', 'SITE = r"C:\\Kimi\\raschet"'),
        ('PARTS = r"C:\\Kimi\\raschet-redesign\\parts"', 'PARTS = r"C:\\Kimi\\raschet\\_build\\parts"'),
        ('ASSETS_SRC = r"C:\\Kimi\\raschet-redesign\\assets"', 'ASSETS_SRC = r"C:\\Kimi\\raschet\\_build\\assets"'),
    ],
    r"C:\Kimi\raschet\_build\build\test_site.py": [
        ('SITE = r"C:\\Kimi\\raschet-site"', 'SITE = r"C:\\Kimi\\raschet"'),
    ],
}

for path, subs in JOBS.items():
    t = io.open(path, encoding="utf-8").read()
    for old, new in subs:
        if old in t:
            t = t.replace(old, new)
            print("OK  ", path.split("\\")[-1], "|", new[:55])
        else:
            print("MISS", path.split("\\")[-1], "|", old[:55])
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)
