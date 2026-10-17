# -*- coding: utf-8 -*-
# Кнопки категорий в шапке → ссылки на разделы каталога (hover открывает, клик ведёт).
import io

P = r"C:\Kimi\raschet\_build\parts\header.html"
t = io.open(P, encoding="utf-8").read()

pairs = [
    ("Финансы", "finance"),
    ("Недвижимость и налоги", "realty"),
    ("Труд и соцзащита", "labor"),
    ("Авто", "auto"),
    ("Юридические", "legal"),
    ("Математика", "math"),
]
n = 0
for name, sec in pairs:
    old = '<button class="nav-cat-btn" type="button" aria-haspopup="true" aria-expanded="false">' + name + " "
    new = '<a class="nav-cat-btn" href="index.html#%s" aria-haspopup="true" aria-expanded="false">' % sec + name + " "
    if old in t:
        t = t.replace(old, new, 1)
        n += 1

# закрывающие </button> шести категорий (у «Ещё» остаётся <button>)
# паттерн: шеврон-svg + </button> перед nav-cat-panel
t = t.replace('</svg></button>\n        <div class="nav-cat-panel">',
              '</svg></a>\n        <div class="nav-cat-panel">')

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("converted categories:", n)
print("nav-cat-btn as <a>:", t.count('<a class="nav-cat-btn"'))
print("nav-cat-btn as <button>:", t.count('<button class="nav-cat-btn"'))
