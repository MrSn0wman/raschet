# -*- coding: utf-8 -*-
# Перенос карточки «Сложный процент» из секции Разное в Финансы на главной.
import io
import re

P = r"C:\Kimi\raschet\index.html"
t = io.open(P, encoding="utf-8").read()

# 1. Вытащить карточку
m = re.search(r'(?s)[ \t]*<a class="calc-item" href="slozhnyy-procent/">.*?</a>\n', t)
assert m, "card not found"
card = m.group(0)
t = t.replace(card, "", 1)

# 2. Вставить в конец calc-list секции Финансы
fin = re.search(r'(?s)(<section class="section" id="finance">.*?<div class="calc-list calc-list--dense">\n)(.*?)(      </div>)', t)
assert fin, "finance section not found"
t = t[:fin.start(2)] + fin.group(2) + card.rstrip("\n") + "\n" + t[fin.start(2) + len(fin.group(2)):]

# 3. Лиде секции Разное без сложного процента
t = t.replace("Единицы, сложный процент, скидки, чаевые.", "Единицы, скидки, чаевые.")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
n_fin = len(re.findall(r'(?s)<section class="section" id="finance">.*?</section>', t))
print("ok. finance sections:", n_fin)
print("card in finance:", "slozhnyy-procent" in re.search(r'(?s)<section class="section" id="finance">.*?</section>', t).group(0))
print("card in misc:", "slozhnyy-procent" in re.search(r'(?s)<section class="section" id="misc">.*?</section>', t).group(0))
